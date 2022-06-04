import os
from time import time
from collections import defaultdict
from chardet import detect
from urllib.parse import quote_from_bytes
from rest_framework.views import APIView
from module.response import OK, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CREATED, NOT_FOUND
from module.validator import Validator, Json, Path
from module.decorator import login_required, sa_required, get_user
from module.environ import get_db, get_table, run_problem
from module.query_analyzer.mysql.query_validator import SELECTQueryValidator
from module.query_analyzer.mysql.query_explainer import QueryExplainer
from app_main.models import (
    ProblemGroup, Problem, Env, 
    Warning, WarningBelongProblem, UserBelongClass, 
    UserSolveProblem, WarningBelongUp
)
from app_main.serializer import (
    WarningSrz, ProblemSrz, ProblemInGroupSrz,
    MyProblemSrz, UserWarningSrz, USPSrz,
    ClassEnvSrz, AllInProblemSrz
)
from django.db.models import F, Q, Count
from django.utils import timezone
from django_jwt_extended import jwt_required


class ProblemsInPgroupView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        특정 문제집의 문제 목록 반환 API
        학생은 활성화 체크
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('pgroup_id', int),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:
            check_user = UserBelongClass.objects.filter(
                user_id=user.id,
                class_id__problemgroup__id=data['pgroup_id'],
            ).first()
            if not check_user:
                return FORBIDDEN("can't find class.")
                
        if user.is_sa or check_user.is_admin:   #관리자
            problems = Problem.objects.filter(
                pg_id=data['pgroup_id']
            ).annotate(
                problem_warnings=Count('warningbelongproblem'),
            ).order_by('id')
        else:   #학생
            problems = Problem.objects.filter(
                Q(pg_id=data['pgroup_id']),
                Q(pg_id__class_id__activate=1),
                (
                    (Q(pg_id__activate_start=None) | Q(pg_id__activate_start__lt=timezone.now())) &
                    (Q(pg_id__activate_end=None) | Q(pg_id__activate_end__gt=timezone.now()))
                )   #분반 활성화, 문제집 활성화 체크
            ).annotate(
                problem_warnings=Count('warningbelongproblem'),
            ).order_by('id')
        p_id = list(problems.values_list('id',flat=True))

        usp = UserSolveProblem.objects.filter(
            p_id__in=p_id,  #문제집에 속한 문제들중
            user_id=user.id,    #내가 푼 문제이며
            submit=True,    #제출한 문제만
        ).annotate(
            user_warnings=Count('warningbelongup'),
            problem_id=F('p_id__id')
        ).values(
            'id',
            'problem_id',
            'accuracy',
            'created_at',
            'user_warnings'
        ).order_by('p_id__id', '-accuracy', '-created_at')
        
        """
        usp에 같은 p_id가 여러 개 존재함.
        distinct가 불가능 -> created_at이 각자 다르기 때문
        status 표시는 정답, 오답, 미제출 순서로 우선순위 정해지고,
        그 중에서 가장 최근에 푼 문제로 보여줘야함.
        따라서 우선순위 기준으로 order_by 해주고,
        밑에 반복문에서 처음 나오는 p_id만 problems에 넣어줌.
        """

        for obj in usp:
            if obj['problem_id'] in p_id:
                for p in problems:
                    if p.id == obj['problem_id']:
                        p.user_warnings = obj['user_warnings']
                        p.status = 'Correct' if obj['accuracy'] else 'Wrong Answer'
                        p_id.pop(p_id.index(p.id)) #같은 p_id는 못 들어가도록 pop
                        break

        for p in problems:   #No Submit
            if p.id in p_id:
                p.status = 'No Submit'
                p.user_warnings = 0

        problem_srz = ProblemInGroupSrz(problems, many=True)
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
            envbelongclass__class_id=data['class_id'],  #분반에 연결된 env만
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
        수정용 문제 반환 API
        SA, 교수, 조교만 호출 가능
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
            check_user = UserBelongClass.objects.filter(
                user_id=user.id,
                class_id=data['class_id']
            ).first()
            if not check_user:
                return FORBIDDEN("can't find class.")
            if not check_user.is_admin:
                return FORBIDDEN("student can't access.")
        
        problem = Problem.objects.filter(
            id=data['problem_id'],
            pg_id__class_id=data['class_id']
        ).select_related('env_id__user_id').first()
        if not problem:
            return NOT_FOUND
    
        if problem.env_id:
            problem.env_id.owner = problem.env_id.user_id.id
            problem.env_id.status = problem.env_id.result

        env_srz = ClassEnvSrz(problem.env_id).data
        problem_srz = AllInProblemSrz(problem).data
        problem_srz['env'] = env_srz if env_srz['id'] else None
        
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
                envbelongclass__class_id=data['class_id'],
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
            ).select_related('env_id').first()
        else:   #학생
            problem = Problem.objects.filter(
                Q(id=data['problem_id']),
                Q(pg_id__class_id__activate=1),
                (
                    (Q(pg_id__activate_start=None) | Q(pg_id__activate_start__lt=timezone.now())) &
                    (Q(pg_id__activate_end=None) | Q(pg_id__activate_end__gt=timezone.now()))
                )
            ).select_related('env_id').first()   #분반 활성화, 문제집 활성화 체크
        if not problem:
            return FORBIDDEN("can't find problem.")
        
        if not data['query']:
            return BAD_REQUEST("query does not exist.")
        query = data['query'].lower().replace('\xa0', ' ')

        if not problem.env_id:
            return FORBIDDEN("can't find env.")

        status, query_result = run_problem(problem.env_id, query)

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


class EnvRunView(APIView):

    @jwt_required()
    @login_required()
    def post(self, request, **path):
        """
        문제 생성 시, 문제 실행 API
        SA, 교수, 조교만 호출 가능
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Path('env_id', int),
                Json('query', str)
            ])
        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:
            check_user = UserBelongClass.objects.filter(
                user_id=user.id,
                class_id=data['class_id']
            ).first()
            if not check_user:
                return FORBIDDEN("can't find class.")
            if not check_user.is_admin:
                return FORBIDDEN("student can't access.")
        
        env = Env.objects.filter(
            id=data['env_id'],
            envbelongclass__class_id=data['class_id']
        ).first()
        if not env:
            return FORBIDDEN("can't find env.")

        if not data['query']:
            return BAD_REQUEST("query does not exist.")
        query = data['query'].lower().replace('\xa0', ' ')

        status, query_result = run_problem(env, query)
        
        return OK({
            'status': status,
            'query_result': query_result
        })


class ProblemSubmitView(APIView):

    @jwt_required()
    @login_required()
    def post(self, request, **path):
        """
        문제 제출 API
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
            ).prefetch_related(
                'warningbelongproblem_set'
            ).select_related('env_id').first()
        else:   #학생
            problem = Problem.objects.filter(
                Q(id=data['problem_id']),
                Q(pg_id__class_id__activate=1),
                (
                    (Q(pg_id__activate_start=None) | Q(pg_id__activate_start__lt=timezone.now())) &
                    (Q(pg_id__activate_end=None) | Q(pg_id__activate_end__gt=timezone.now()))
                )
            ).prefetch_related(
                'warningbelongproblem_set'
            ).select_related('env_id').first()   #분반 활성화, 문제집 활성화 체크

        if not problem:
            return FORBIDDEN("can't find problem.")
        
        if not data['query']:
            return BAD_REQUEST("query does not exist.")
        query = data['query'].lower().replace('\xa0', ' ')

        if not problem.env_id:
            return FORBIDDEN("can't find env.")

        warnings = problem.warningbelongproblem_set.values_list(
            'warning_id__id',
            flat=True
        )
        
        db = get_db(
            user=problem.env_id.account_name,
            passwd=problem.env_id.account_pw
        )
        cursor = db.cursor()
        db.select_db(problem.env_id.db_name)

        explain = QueryExplainer(
            uri="mysql://" + str(problem.env_id.account_name) + ":" +
                str(problem.env_id.account_pw) + "@" +
                os.environ['SSQL_ORIGIN_MYSQL_HOST'] + ":" +
                os.environ['SSQL_ORIGIN_MYSQL_PORT'] + "/" +
                str(problem.env_id.db_name)
        )
        res = explain.explain_query(query)

        if res.report_type == 'validation_report':  #올바르지 않은 쿼리
            usp = UserSolveProblem(
                p_id=problem,
                user_id=user,
                query=query,
                accuracy=False,
                submit=True,
            )
            usp.save()  #실행이 불가능한 쿼리는 warning도 걸리지 않음.

            return OK({
                'status': False,
                'accuracy': False,
                'warnings': [],
            })
        else:
            answer = problem.answer.lower().replace('\n', '').replace(' ','')
            tic = time()
            cursor.execute(query)
            toc = time()
            query_result = cursor.fetchall()

            cursor.execute(problem.answer.lower())
            answer_result = cursor.fetchall()

            if 'orderby' in answer: #정답에서 order by를 요구할 때
                accuracy = True if query_result == answer_result else False
            else:
                #해시화해서 비교
                hash_dict = defaultdict(str)
                p_answer = set()
                for id, result in enumerate(answer_result):
                    hash_dict[str(result)] = f"HASH{id}"
                    p_answer.add(f"HASH{id}")

                u_answer = set()
                for result in query_result:
                    u_answer.add(hash_dict[str(result)])
                    
                accuracy = True if u_answer == p_answer else False  
            
            checked_warnings = [warning.code for warning in res.warnings]

            if (toc-tic) > problem.timelimit:   #시간초과
                checked_warnings.append('time_limit')
            
            user_warnings = Warning.objects.filter(
                id__in=warnings,    #문제에 걸린 warning 중에서
                name__in=checked_warnings   #user가 걸린 warning 반환
            )

            usp = UserSolveProblem(
                p_id=problem,
                user_id=user,
                query=query,
                accuracy=accuracy,
                submit=True,
            )
            usp.save()

            for warning in user_warnings:
                wbp = WarningBelongUp(
                    up_id=usp,
                    warning_id=warning
                )
                wbp.save()

            result = {
                'status': True,
                'accuracy': accuracy,
                'warnings': WarningSrz(user_warnings, many=True).data
            }
            return OK(result)


class ReadProblemView(APIView):

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
            ).prefetch_related(
                'usersolveproblem_set'
            ).first()
        else:   #학생
            problem = Problem.objects.filter(
                Q(id=data['problem_id']),
                Q(pg_id__class_id__activate=1),
                (
                    (Q(pg_id__activate_start=None) | Q(pg_id__activate_start__lt=timezone.now())) &
                    (Q(pg_id__activate_end=None) | Q(pg_id__activate_end__gt=timezone.now()))
                )
            ).prefetch_related(
                'usersolveproblem_set'
            ).first()   #분반 활성화, 문제집 활성화 체크
        if not problem:
            return FORBIDDEN("can't find problem.")

        result = problem.usersolveproblem_set.filter(
            user_id=user.id,
            submit=1
        ).order_by('-created_at').first()

        problem_srz = ProblemSrz(problem).data
        problem_srz['latest_query'] = result.query if result else None
        problem_srz['warnings'] = []

        if result:
            warnings = WarningBelongUp.objects.filter(
                up_id=result.id
            ).annotate(
                usp_id=F('up_id__id'),
                name=F('warning_id__name'),
                content=F('warning_id__content')
            )
            warning_srz = UserWarningSrz(warnings, many=True).data

            for w in warning_srz:
                problem_srz['warnings'].append({
                    'name': w['name'],
                    'content': w['content']
                })     

        if problem.env_id:
            desc_table, select_table = get_table(problem.env_id, problem.answer)

        problem_srz['desc_table'] = desc_table if desc_table else []
        problem_srz['select_table'] = select_table if select_table else []
        return OK(problem_srz)


class MyProblemView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        내가 푼 문제 반환
        """

        user = get_user(request)
    
        problems = Problem.objects.filter(
            usersolveproblem__user_id=user.id,
            usersolveproblem__submit=True,
        ).order_by('id').distinct()
        p_id = list(problems.values_list('id',flat=True))

        usp = UserSolveProblem.objects.filter(
            p_id__in=p_id,
            user_id=user.id,
            submit=True,
        ).annotate(
            problem_id=F('p_id__id')
        ).order_by('p_id__id', '-accuracy', '-created_at')

        orm_list = []
        for obj in usp:
            if obj.problem_id in p_id:
                for p in problems:
                    if p.id == obj.problem_id:
                        orm_list.append(obj.id)
                        p.accuracy = obj.accuracy
                        p.usp_id = obj.id
                        p_id.pop(p_id.index(p.id))
                        break
        
        warnings = WarningBelongUp.objects.filter(
            up_id__in=orm_list
        ).annotate(
            usp_id=F('up_id__id'),
            name=F('warning_id__name'),
            content=F('warning_id__content')
        ).order_by('up_id')

        problem_srz = MyProblemSrz(problems, many=True).data
        warning_srz = UserWarningSrz(warnings, many=True).data

        for p in problem_srz:
            p['warnings'] = []
            for w in warning_srz:
                if p['usp_id'] == w['usp_id']:
                    p['warnings'].append({
                        'name': w['name'],
                        'content': w['content']
                    })                    
        
        correct = []
        wrong = []
        for p in problem_srz:
            if p['accuracy']:
                correct.append(p)
            else:
                wrong.append(p)
        
        result = {
            'correct': correct,
            'wrong': wrong
        }
        return OK(result)


class UserSolveProblemView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        특정 문제 반환 API
        usp_id가 주어진 경우
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('usp_id', int),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:
            check_user = UserBelongClass.objects.filter(
                user_id=user.id,
                class_id__problemgroup__problem__usersolveproblem=data['usp_id'],
            ).first()
            if not check_user:
                return FORBIDDEN("can't find class or problem.")

        if user.is_sa or check_user.is_admin:   #관리자
            usp = UserSolveProblem.objects.filter(
                id=data['usp_id']
            ).annotate(
                problem_id=F('p_id__id'),
                title=F('p_id__title'),
                content=F('p_id__content'),
                env_id=F('p_id__env_id'),
                answer=F('p_id__answer')
            ).first()
        else:   #학생
            usp = UserSolveProblem.objects.filter(
                id=data['usp_id'],
                user_id=user.id,
            ).annotate(
                problem_id=F('p_id__id'),
                title=F('p_id__title'),
                content=F('p_id__content'),
                env_id=F('p_id__env_id'),
                answer=F('p_id__answer')
            ).first()
        if not usp:
            return FORBIDDEN("can't find problem.")

        usp_srz = USPSrz(usp).data
        usp_srz['id'] = usp_srz['problem_id']
        del usp_srz['problem_id']

        warnings = WarningBelongUp.objects.filter(
            up_id=data['usp_id']
        ).annotate(
            usp_id=F('up_id__id'),
            name=F('warning_id__name'),
            content=F('warning_id__content')
        )
        warning_srz = UserWarningSrz(warnings, many=True).data

        usp_srz['warnings'] = []
        for w in warning_srz:
            usp_srz['warnings'].append({
                'name': w['name'],
                'content': w['content']
            })
        
        env = Env.objects.filter(
            id=usp.env_id
        ).first()

        if env:
            desc_table, select_table = get_table(env, usp.answer)
        
        usp_srz['desc_table'] = desc_table if desc_table else []
        usp_srz['select_table'] = select_table if select_table else []
        return OK(usp_srz)

    

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
