from django.db import migrations, models


def deduplicate_slugs(apps, schema_editor):
    projects = apps.get_model('portfolio', 'Projects').objects.using(schema_editor.connection.alias)
    used = set(projects.values_list('slug', flat=True))
    seen = set()
    for project in projects.order_by('pk').iterator():
        if project.slug in seen:
            suffix = f'-{project.pk}'
            candidate = project.slug[:100 - len(suffix)] + suffix
            while candidate in used:
                suffix += '-copy'
                candidate = project.slug[:100 - len(suffix)] + suffix
            projects.filter(pk=project.pk).update(slug=candidate)
            used.add(candidate)
        seen.add(project.slug)


class Migration(migrations.Migration):
    dependencies = [('portfolio', '0008_aboutme_email_aboutme_location_aboutme_phone')]
    operations = [
        migrations.RunPython(deduplicate_slugs, migrations.RunPython.noop),
        migrations.AlterField('projects', 'slug', models.SlugField(max_length=100, unique=True)),
    ]
