import os
from django.db import connection
from datetime import datetime
from rest_framework.views import APIView
from module.response import OK, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CREATED
from module.validator import Validator, Json, Path
from module.decorator import login_required, sa_required, get_user
from module.environ import get_db
from module.query_analyzer.mysql.query_validator import SELECTQueryValidator
from app_main.models import ProblemGroup, Problem, Env, Warning, WarningBelongProblem, UserBelongClass, UserSolveProblem
from app_main.serializer import WarningSrz, ProblemSrz
from django.db.models import F, Q
from django.utils import timezone
from django_jwt_extended import jwt_required


class ProblemsInPgroupView(APIView):

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

        pgroup = ProblemGroup.objects.filter(
            id=data['pgroup_id'],
            class_id=data['class_id']
        ).first()
        if not pgroup:
            return FORBIDDEN("can't find pgroup.")

        env = Env.objects.filter(
            id=data['env_id'],
            result='success'    #성공한 env만 적용.
        ).first()
        if not env:
            return FORBIDDEN("can't find env.")
        
        problem = Problem(
            pg_id=pgroup,
            env_id=env,
            title=data['title'],
            content=data['content'],
            answer=data['answer'],
            timelimit=data['timelimit'] or 10   #기본값 10초
        )  
        problem.save()

        if data['warnings']:
            warnings = Warning.objects.filter(id__in=data['warnings'])
            for warning in warnings:
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
        학생인 경우, 해당 문제가 속한 문제집 활성화 여부 체크!
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('problem_id', int)
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if user.is_sa:  #관리자
            problem = Problem.objects.filter(
                id=data['problem_id']
            ).prefetch_related(
                'usersolveproblem_set'
            ).first()
        else:   #분반 소속
            problem = Problem.objects.filter(
                id=data['problem_id'],
                pg_id__class_id__userbelongclass__user_id=user.id,
            ).select_related(
                'pg_id__class_id'
            ).prefetch_related(
                'usersolveproblem_set'
            ).first()
        if not problem:
            return FORBIDDEN("can't find problem.")
        
        if UserBelongClass.objects.filter(
            class_id=problem.pg_id.class_id.id,
            user_id=user.id,
            type='st'
        ).exists():     #학생이면
        
            if not problem.pg_id.class_id.activate or  (#분반이 비활성화이거나
                (
                    problem.pg_id.activate_start!=None and
                    (problem.pg_id.activate_start==datetime(1997,12,8,0,0,0) or
                    problem.pg_id.activate_start > timezone.now())
                ) or
                (
                    problem.pg_id.activate_end!=None and
                    (problem.pg_id.activate_end==datetime(1997,12,8,0,0,0) or 
                    problem.pg_id.activate_end < timezone.now())
                )  #문제집이 비활성화이면
            ):
                return FORBIDDEN("can't find problem.")

        result = problem.usersolveproblem_set.filter(
            submit=1
        ).order_by('-created_at').first()

        problem_srz = ProblemSrz(problem).data
        problem_srz['latest_query'] = result.query if result else None

        return OK(problem_srz)


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

        problem = Problem.objects.filter(
            id=data['problem_id'],
            pg_id__class_id=data['class_id']
        ).first()
        if not problem:
            return FORBIDDEN("can't find problem.")

        if data['env_id']:
            env = Env.objects.filter(
                id=data['env_id'],
                result='success'
            ).first()
            if not env:
                return FORBIDDEN("can't find env.")

            problem.env_id = env

        problem.title = data['title'] or problem.title
        problem.content = data['content'] or problem.content
        problem.answer = data['answer'] or problem.answer
        problem.timelimit = data['timelimit'] or problem.timelimit

        if data['warnings'] is not None:
            wbp = WarningBelongProblem.objects.filter(  #연결된 warning 불러오기.
                p_id=problem.id
            )
            if wbp:
                wbp.delete()    #기존에 연결된 warning은 제거

            warnings = Warning.objects.filter(id__in=data['warnings'])              
            for warning in warnings:
                new_wbp = WarningBelongProblem(
                    p_id=problem,
                    warning_id=warning
                )
                new_wbp.save()
        problem.save()
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

        problem = Problem.objects.filter(
            id=data['problem_id'],
            pg_id__class_id=data['class_id']
        ).first()
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
        학생은 활성화 체크
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('problem_id', int),
                Json('query', str)
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:
            check_user = UserBelongClass.objects.filter(
                user_id=user.id,
                class_id__problemgroup__problem=data['problem_id'],
            ).first()
            if not check_user:
                return FORBIDDEN("can't find class.")
        
        if user.is_sa or check_user.is_admin:   #관리자
            problem = Problem.objects.filter(
                id=data['problem_id']
            ).first()
        else:   #학생
            problem = Problem.objects.filter(
                Q(id=data['problem_id']),
                Q(pg_id__class_id__activate=1),
                (
                    (Q(pg_id__activate_start=None) | Q(pg_id__activate_start__lt=timezone.now())) &
                    (Q(pg_id__activate_end=None) | Q(pg_id__activate_end__gt=timezone.now()))
                )
            ).first()   #분반 활성화, 문제집 활성화 체크
        if not problem:
            return FORBIDDEN("can't find problem.")
        
        if not data['query']:
            return BAD_REQUEST("query does not exist.")

        queries = data['query'].split(';')
        for i in range(len(queries)-1): #세미콜론을 판단하기 위한 작업
            queries[i] += ';'

        query = queries[0]
        no_semicolon = False
        if not query.rstrip().endswith(';'):
            no_semicolon = True

        if not problem.env_id:
            return FORBIDDEN("can't find env.")

        db = get_db(
            user=problem.env_id.account_name,
            passwd=problem.env_id.account_pw
        )
        cursor = db.cursor()
        db.select_db(problem.env_id.db_name)

        validator = SELECTQueryValidator(
            uri="mysql://" + str(problem.env_id.account_name) + ":" +
                str(problem.env_id.account_pw) + "@" +
                os.environ['SSQL_ORIGIN_MYSQL_HOST'] + ":" +
                os.environ['SSQL_ORIGIN_MYSQL_PORT'] + "/" +
                str(problem.env_id.db_name)
        )
        validator_result = validator.check_query(query=query)

        status = True
        if validator_result.result:
            try:
                cursor.execute(query)
                query_result = cursor.fetchall()
            except Exception as error:
                status = False
                query_result = str(error)
        else:
            status = False
            query_result = validator_result.msg
            query_result = query_result.replace(f"{problem.env_id.db_name}.", "")
            query_result = query_result.replace(problem.env_id.db_name, "")

        usp = UserSolveProblem(
            p_id=problem,
            user_id=user,
            query=query
        )
        usp.save()

        if no_semicolon:
            return OK({
                'status': True,
                'query_result': "query must be end with semicolon."
            })
        
        return OK({
            'status': status,
            'query_result': query_result
        })


class WarningView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        warning 종류 반환 API
        """
        
        warnings = Warning.objects.all()
        warnings_srz = WarningSrz(warnings, many=True)
        return OK(warnings_srz.data)


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
