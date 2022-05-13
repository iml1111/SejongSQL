from rest_framework.views import APIView
from module.response import OK, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CREATED
from module.validator import Validator, Json, Path
from module.decorator import login_required, sa_required, get_user
from module.environ import connect_to_environ
from app_main.models import Class, ProblemGroup, Problem, Env, TableBelongEnv, UserSolveProblem, Warning, WarningBelongProblem, WarningBelongUp
from app_main.serializer import ProblemGroupSrz
from django.db.models import F, Q
from django.utils import timezone
from django_jwt_extended import jwt_required


class ProblemsInPgroupView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        특정 문제집의 문제 목록 반환 API
        학생인 경우, 문제집 활성화 여부 체크!
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
            if not ubc.is_admin:    #학생인 경우 활성화된 문제집인지 체크
                pgroup = ProblemGroup.objects.filter(
                    Q(id=data['pgroup_id']),
                (
                    Q(activate_start=None) |
                    Q(activate_start__lt=timezone.now())   #lt(less than)
                ),
                (
                    Q(activate_end=None) | 
                    Q(activate_end__gt=timezone.now())   #gt(greater than)
                )
                ).first()
                if not pgroup:
                    return FORBIDDEN("can't find pgroup or pgroup is deactivated.")
            
                problems = Problem.objects.filter(
                    pg_id=data['pgroup_id'],

                )
                

                
        
        problems = Problem.objects.filter(pg_id=data['pgroup_id'])
        if not problems:
            return FORBIDDEN("can't find problems.")                                                            
        problem_srz = ProblemSrz(problems, many=True)

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
                Json('timelimit', int, optional=True),
                Json('warnings', list)
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:    
            ubc = user.userbelongclass_set.filter(class_id=data['class_id']).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
            if not ubc.is_admin:                
                return BAD_REQUEST("student can't access.")

        pgroup = ProblemGroup.objects.filter(id=data['pgroup_id']).first()
        if not pgroup:
            return FORBIDDEN("can't find pgroup.")

        env = Env.objects.filter(
            id=data['env_id'],
            result='success'    #성공한 env만 적용.
        ).first()
        if not env:
            return FORBIDDEN("can't find env.")

        warning_list = []
        for warning in data['warnings']:
            warning_id = Warning.objects.filter(id=warning).first()
            if not warning_id:
                return FORBIDDEN("can't find warning.")
            
            warning_list.append(warning_id)

        problem = Problem(
            pg_id=pgroup,
            env_id=env,
            title=data['title'],
            content=data['content'],
            answer=data['answer'],
            timelimit=data['timelimit'] or 10   #기본값 10초
        )  
        problem.save()

        for warning in warning_list:
            wbp = WarningBelongProblem(
                p_id=problem,
                warning_id=warning
            )
            wbp.save()

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
                return BAD_REQUEST("student can't access.")   #바꿔야함


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
                Json('warnings', list, optional=True)
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:    
            ubc = user.userbelongclass_set.filter(class_id=data['class_id']).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
            if not ubc.is_admin:                
                return BAD_REQUEST("student can't access.")

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
        
        if data['warnings']:
            wbp = WarningBelongProblem.objects.filter(  #연결된 warning 불러오기.
                p_id=problem.id
            ).annotate(
                warning=F('warning_id__id')
            ).values('warning')
            check_warning = [warning['warning'] for warning in wbp]

            warning_list = []
            for warning in data['warnings']:
                warning_id = Warning.objects.filter(id=warning).first()
                if not warning_id:
                    return FORBIDDEN("can't find warning.")
                
                if warning not in check_warning:    #이미 연결된 warning은 제외하고 추가.
                    warning_list.append(warning_id)

            for warning in warning_list:
                new_wbp = WarningBelongProblem(
                    p_id=problem,
                    warning_id=warning
                )
                new_wbp.save()

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
                return BAD_REQUEST("student can't access.")

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

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Path('problem_id', int),
                Json('query', str)
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:    
            ubc = user.userbelongclass_set.filter(class_id=data['class_id']).first()
            if not ubc:
                return FORBIDDEN("can't find class.")

        problem = Problem.objects.filter(id=data['problem_id']).first()
        if not problem:
            return FORBIDDEN("can't find problem.")

        if not data['query']:
            return BAD_REQUEST("query does not exist.")

        env_table = TableBelongEnv.objects.filter(env_id=problem.env_id)
        if not env_table:
            return FORBIDDEN("env in problem does not exist.")

        query = data['query']
        for table in env_table:
            query = query.replace(table.table_nickname, table.table_name)

        db = connect_to_environ()
        cur = db.cursor()
        

        

        
        


        



class ProblemSubmitView(APIView):

    @jwt_required()
    @login_required()
    def post(self, request, **path):
        """
        문제 제출 API
        """


class CreateWarningView(APIView):

    @jwt_required()
    @login_required()
    @sa_required
    def post(self, request, **path):
        """
        warning 테이블 생성 API
        """

        validator = Validator(
            request, path, params=[
                Json('warnings', dict)
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data
        
        for key, value in data['warnings'].items():
            warning = Warning(
                name=key,
                content=value
            )
            warning.save()
        
        return CREATED()
