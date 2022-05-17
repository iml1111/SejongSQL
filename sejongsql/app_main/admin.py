from django.contrib import admin
from .models import (
    User, Class, UserBelongClass,
    Problem, ProblemGroup, UserSolveProblem,
    WarningMatchProblem, WarningMatchUp, ExplainWarning,
    Env, EnvBelongClass, EnvBelongTable,
    Queue
)

class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'sejong_id', 'role']

class UBCAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'class_id', 'type']

class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'semester', 'comment', 'activate']

class ProblemGroupAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'class_id', 'name', 'comment', 'exam',
        'activate_start', 'activate_end'
    ]

class EnvAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'name', 'db_name', 'file_name', 'result']

class EBCAdmin(admin.ModelAdmin):
    list_display = ['id', 'env_id', 'class_id']

class EBTAdmin(admin.ModelAdmin):
    list_display = ['id', 'env_id', 'table_name']

class QueueAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_id', 'type', 'type_id', 'status']

admin.site.register(User, UserAdmin)
admin.site.register(Class, ClassAdmin)
admin.site.register(UserBelongClass, UBCAdmin)
admin.site.register(Problem)
admin.site.register(ProblemGroup, ProblemGroupAdmin)
admin.site.register(UserSolveProblem)
admin.site.register(WarningMatchProblem)
admin.site.register(WarningMatchUp)
admin.site.register(ExplainWarning)
admin.site.register(Env, EnvAdmin)
admin.site.register(EnvBelongClass, EBCAdmin)
admin.site.register(EnvBelongTable, EBTAdmin)
admin.site.register(Queue, QueueAdmin)
