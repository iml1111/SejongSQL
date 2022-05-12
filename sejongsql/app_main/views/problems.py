from rest_framework.views import APIView
from module.response import OK, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CREATED
from module.validator import Validator, Json, Path
from module.decorator import login_required, get_user
from app_main.models import Class, ProblemGroup, Problem, Env, UserSolveProblem
from app_main.serializer import ProblemGroupSrz
from django.db.models import Q
from django_jwt_extended import jwt_required


class ProblemsInPgroupView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        특정 문제집의 문제 목록 반환 API
        학생인 경우, 활성화 여부 체크!
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Path('pgroup_id', int)
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:    
            ubc = user.userbelongclass_set.filter(class_id=data['class_id']).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
            if not ubc.is_admin:                
                return FORBIDDEN("student can't access.")   #바꿔야함
        
        problems = Problem.objects.filter(pg_id=data['pgroup_id'])  #문제 반환할 때, 활성화된 분반인지, 활성화된 문제집인지 확인 해야하나..?
                                                                    #시험문제같은 중요한 문제가 있으므로 반드시 활성화 여부를 확인해야 할듯. 대신 문제집 활성화 정도면..?
        problem_srz = ProblemSrz(problems, many=True)   #노션 api 확인! 문제정답여부 어케처리할지

        return OK(problem_srz.data)


    @jwt_required()
    @login_required()
    def post(self, request, **path):
        """
        문제 생성 API
        SA, 교수, 조교 호출 가능
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Path('pgroup_id', int),
                Json('env_id', int),
                Json('title', str),
                Json('content', str),
                Json('answer', str),
                Json('timelimit', int),
                Json('keyword', list)
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:    
            ubc = user.userbelongclass_set.filter(class_id=data['class_id']).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
            if not ubc.is_admin:                
                return FORBIDDEN("student can't access.")

        pgroup = ProblemGroup.objects.filter(id=data['pgroup_id']).first()
        if not pgroup:
            return FORBIDDEN("can't find pgroup.")

        env = Env.objects.filter(id=data['env_id']).first()
        if not env:
            return FORBIDDEN("can't find env.")

        problem = Problem(
            pg_id=pgroup,
            env_id=env,
            title=data['title'],
            content=data['content'],
            answer=data['answer'],
            timelimit=data['timelimit']
        )  
        problem.save()

        #keyword는 우리가 explain_warning 테이블에 넣는건가??

        return CREATED()
        

class ProblemView(APIView):
    
    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        특정 문제 반환 API
        학생인 경우, 활성화 여부 체크!
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Path('problem_id', int)
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:    
            ubc = user.userbelongclass_set.filter(class_id=data['class_id']).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
            if not ubc.is_admin:                
                return FORBIDDEN("student can't access.")   #바꿔야함


    @jwt_required()
    @login_required()
    def put(self, request, **path):
        """
        문제 수정 API
        SA, 교수, 조교 호출 가능
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Path('problem_id', int),
                Json('env_id', int, optional=True),
                Json('title', str, optional=True),
                Json('content', str, optional=True),
                Json('answer', str, optional=True),
                Json('timelimit', int, optional=True),
                Json('keyword', list, optional=True)
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:    
            ubc = user.userbelongclass_set.filter(class_id=data['class_id']).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
            if not ubc.is_admin:                
                return FORBIDDEN("student can't access.")

        problem = Problem.objects.filter(id=data['problem_id']).first()
        if not problem:
            return FORBIDDEN("can't find problem.")

        if data['env_id']:
            env = Env.objects.filter(id=data['env_id']).first()
            if not env:
                return FORBIDDEN("can't find env.")

            problem.env_id = env

        problem.title = data['title'] or problem.title
        problem.content = data['content'] or problem.content
        problem.answer = data['answer'] or problem.answer
        problem.timelimit = data['timelimit'] or problem.timelimit
        problem.keyword = data['keyword'] or problem.keyword

        return CREATED()

    
    @jwt_required()
    @login_required()
    def delete(self, request, **path):
        """
        문제 삭제 API
        SA, 교수, 조교 호출 가능
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Path('problem_id', int)
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:    
            ubc = user.userbelongclass_set.filter(class_id=data['class_id']).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
            if not ubc.is_admin:                
                return FORBIDDEN("student can't access.")

        problem = Problem.objects.filter(id=data['problem_id']).first()
        if not problem:
            return FORBIDDEN("can't find problem.")
        
        problem.delete()
        return NO_CONTENT


class ProblemRunView(APIView):

    @jwt_required()
    @login_required()
    def post(self, request, **path):
        """
        문제 실행 API
        """



class ProblemSubmitView(APIView):

    @jwt_required()
    @login_required()
    def post(self, request, **path):
         """
        문제 제출 API
        """