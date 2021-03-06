from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ApiLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.CharField(max_length=100)),
                ('type', models.CharField(max_length=100)),
                ('ip', models.CharField(max_length=100)),
                ('uri', models.CharField(max_length=100)),
                ('body', models.CharField(max_length=1000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'ssql_api_log',
            },
        ),
        migrations.CreateModel(
            name='Class',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('semester', models.CharField(max_length=100)),
                ('comment', models.CharField(max_length=1000)),
                ('activate', models.BooleanField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'ssql_class',
            },
        ),
        migrations.CreateModel(
            name='Env',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('db_name', models.CharField(max_length=100)),
                ('file_name', models.CharField(max_length=100)),
                ('result', models.CharField(default='working', max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'ssql_env',
            },
        ),
        migrations.CreateModel(
            name='Problem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('content', models.TextField(max_length=20000)),
                ('answer', models.CharField(max_length=1000)),
                ('timelimit', models.FloatField(default=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('env_id', models.ForeignKey(db_column='env_id', null=True, on_delete=django.db.models.deletion.SET_NULL, to='app_main.env')),
            ],
            options={
                'db_table': 'ssql_problem',
            },
        ),
        migrations.CreateModel(
            name='Queue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.CharField(max_length=100)),
                ('type', models.CharField(max_length=100)),
                ('type_id', models.IntegerField()),
                ('status', models.CharField(default='working', max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'ssql_queue',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('pw', models.CharField(max_length=88)),
                ('sejong_id', models.CharField(default=None, max_length=100, null=True)),
                ('name', models.CharField(max_length=100)),
                ('role', models.CharField(default='general', max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('pw_updated_at', models.DateTimeField()),
            ],
            options={
                'db_table': 'ssql_user',
            },
        ),
        migrations.CreateModel(
            name='UserSolveProblem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accuracy', models.BooleanField(default=None, null=True)),
                ('submit', models.BooleanField(default=0)),
                ('query', models.CharField(max_length=1000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('p_id', models.ForeignKey(db_column='p_id', null=True, on_delete=django.db.models.deletion.SET_NULL, to='app_main.problem')),
                ('user_id', models.ForeignKey(db_column='user_id', null=True, on_delete=django.db.models.deletion.SET_NULL, to='app_main.user')),
            ],
            options={
                'db_table': 'ssql_user_solve_problem',
            },
        ),
        migrations.CreateModel(
            name='Warning',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('content', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'ssql_warning',
            },
        ),
        migrations.CreateModel(
            name='WarningBelongUp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('up_id', models.ForeignKey(db_column='up_id', null=True, on_delete=django.db.models.deletion.SET_NULL, to='app_main.usersolveproblem')),
                ('warning_id', models.ForeignKey(db_column='warning_id', on_delete=django.db.models.deletion.CASCADE, to='app_main.warning')),
            ],
            options={
                'db_table': 'ssql_warning_belong_up',
            },
        ),
        migrations.CreateModel(
            name='WarningBelongProblem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('p_id', models.ForeignKey(db_column='p_id', on_delete=django.db.models.deletion.CASCADE, to='app_main.problem')),
                ('warning_id', models.ForeignKey(db_column='warning_id', on_delete=django.db.models.deletion.CASCADE, to='app_main.warning')),
            ],
            options={
                'db_table': 'ssql_warning_belong_problem',
            },
        ),
        migrations.CreateModel(
            name='UserBelongClass',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('class_id', models.ForeignKey(db_column='class_id', on_delete=django.db.models.deletion.CASCADE, to='app_main.class')),
                ('user_id', models.ForeignKey(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, to='app_main.user')),
            ],
            options={
                'db_table': 'ssql_user_belong_class',
            },
        ),
        migrations.CreateModel(
            name='ProblemGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('comment', models.CharField(max_length=100)),
                ('exam', models.BooleanField(default=0)),
                ('activate_start', models.DateTimeField(default=None, null=True)),
                ('activate_end', models.DateTimeField(default=None, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('class_id', models.ForeignKey(db_column='class_id', on_delete=django.db.models.deletion.CASCADE, to='app_main.class')),
            ],
            options={
                'db_table': 'ssql_problem_group',
            },
        ),
        migrations.AddField(
            model_name='problem',
            name='pg_id',
            field=models.ForeignKey(db_column='pg_id', null=True, on_delete=django.db.models.deletion.CASCADE, to='app_main.problemgroup'),
        ),
        migrations.CreateModel(
            name='EnvBelongTable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('table_name', models.CharField(max_length=100)),
                ('env_id', models.ForeignKey(db_column='env_id', on_delete=django.db.models.deletion.CASCADE, to='app_main.env')),
            ],
            options={
                'db_table': 'ssql_env_belong_table',
            },
        ),
        migrations.CreateModel(
            name='EnvBelongClass',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('class_id', models.ForeignKey(db_column='class_id', on_delete=django.db.models.deletion.CASCADE, to='app_main.class')),
                ('env_id', models.ForeignKey(db_column='env_id', on_delete=django.db.models.deletion.CASCADE, to='app_main.env')),
            ],
            options={
                'db_table': 'ssql_env_belong_class',
            },
        ),
        migrations.AddField(
            model_name='env',
            name='user_id',
            field=models.ForeignKey(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, to='app_main.user'),
        ),
    ]