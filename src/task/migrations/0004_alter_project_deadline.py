# Generated for optional project deadlines.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task', '0003_project_task_project'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='deadline',
            field=models.DateField(blank=True, null=True),
        ),
    ]
