from django.core.management import call_command
from django.db import migrations


def create_cache(apps, schema_editor):
    call_command('createcachetable', 'portfolio_cache',
                 database=schema_editor.connection.alias, verbosity=0)


class Migration(migrations.Migration):
    dependencies = [('portfolio', '0009_unique_project_slugs')]
    operations = [migrations.RunPython(create_cache, migrations.RunPython.noop)]
