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
from app_main.serializer import ProblemInGroupSrz, WarningSrz, ProblemSrz
from django.db.models import F, Q, Case, When, Count
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
                Path('pgroup_id', int)
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data
        
        if user.is_sa:  #관리자
            problem = Problem.objects.filter(
                pg_id=data['pgroup_id']
            ).first()
        else:   #분반소속
            problem = Problem.objects.select_related(
                'pg_id__class_id'
            ).filter(
                pg_id=data['pgroup_id'],
                pg_id__class_id__userbelongclass__user_id=user.id,
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

        sql = 'SELECT E.id AS p_id, E.title, E.problem_warning_cnt, F.user_warning_cnt, IFNULL(F.accuracy, -1), F.created_at FROM (SELECT A.*, B.problem_warning_cnt FROM ssql_problem AS A LEFT JOIN \
                    (SELECT p_id, COUNT(*) AS problem_warning_cnt FROM ssql_warning_belong_problem GROUP BY p_id) AS B ON A.id = B.p_id WHERE A.pg_id={}) AS E LEFT JOIN \
                        (SELECT id, IFNULL(accuracy, -1) AS accuracy, query, p_id, user_id, IFNULL(D.user_warning_cnt, 0) AS user_warning_cnt, created_at FROM ssql_user_solve_problem AS C LEFT JOIN \
                            (SELECT up_id, COUNT(*) AS user_warning_cnt FROM ssql_warning_belong_up GROUP BY up_id) AS D ON C.id = D.up_id WHERE C.user_id=\'{}\') AS F ON E.id=F.p_id ORDER BY p_id ASC, F.accuracy DESC, F.created_at DESC;'

        cursor = connection.cursor()
        cursor.execute(sql.format(data['pgroup_id'], user.id))
        results = cursor.fetchall()

        # ((3, '테스트', 2, 2, '1', datetime.datetime(2022, 5, 18, 20, 41, 4, 896520)), ((1, 'Book', None, None, None, None),
        from collections import defaultdict
        check = defaultdict(lambda: -1)
        bag = []
        for result in results:
            if check[result[0]] <= result[4]:
                check[result[0]] = result[4]
                bag.append({
                    'id': result[0],
                    'title': result[1],
                    'status': "Correct" if result[4]==1 else "Wrong Answer" if result[4]==0 else "No Submit",
                    'problem_warnings': 0 if result[2] is None else result[2],
                    'user_warnings': 0 if result[3] is None else result[3]
                })
        return OK(bag)


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

        warnings = Warning.objects.filter(id__in=data['warnings'])
        
        problem = Problem(
            pg_id=pgroup,
            env_id=env,
            title=data['title'],
            content=data['content'],
            answer=data['answer'],
            timelimit=data['timelimit'] or 10   #기본값 10초
        )  
        problem.save()

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
            class_id=data['class_id']
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
        
        if data['warnings']:
            wbp = WarningBelongProblem.objects.filter(  #연결된 warning 불러오기.
                p_id=problem.id
            ).annotate(
                warning=F('warning_id__id')
            ).values('warning')
            check_warning = [warning['warning'] for warning in wbp]

            warnings = Warning.objects.filter(id__in=data['warnings'])
            if not warnings:
                return FORBIDDEN("can't find warnings.")                

            for warning in warnings:
                if warning.id not in check_warning: #기존에 없는 warning만 추가
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

        problem = Problem.objects.filter(
            id=data['problem_id'],
            class_id=data['class_id']
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

        if user.is_sa:  #sa인 경우
            problem = Problem.objects.filter(
                id=data['problem_id']
            ).first()
        else:   #분반 소속인 경우
            problem = Problem.objects.filter(
                id=data['problem_id'],
                pg_id__class_id__userbelongclass__user_id=user.id
            ).select_related(
                'pg_id__class_id'
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

        if not data['query']:
            return BAD_REQUEST("query does not exist.")

        query = data['query']
        if not query.endswith(';'):
            return BAD_REQUEST("query needs semicolon ';'")

        if not problem.env_id.id:
            return FORBIDDEN("can't find env.")
        env = Env.objects.filter(id=problem.env_id.id).first()
        if not env:
            return FORBIDDEN("can't find env.")

        db = get_db()
        cursor = db.cursor()
        db.select_db(env.db_name)

        validator = SELECTQueryValidator(
            uri=f"{os.environ['SSQL_ORIGIN_MYSQL_URI']}/{env.db_name}"
        )
        validator_result = validator.check_query(query=query)

        status = True
        if validator_result.result:
            cursor.execute(query)
            query_result = cursor.fetchall()
        else:
            status = False
            query_result = validator_result.msg
            query_result = query_result.replace(f"{env.db_name}.", "")
            query_result = query_result.replace(env.db_name, "")

        usp = UserSolveProblem(
            p_id=problem,
            user_id=user,
            query=query
        )
        usp.save()

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
