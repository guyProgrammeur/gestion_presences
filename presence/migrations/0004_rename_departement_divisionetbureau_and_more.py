# Generated by Django 5.0.14 on 2025-07-03 01:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('presence', '0003_remove_agent_fonction'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Departement',
            new_name='DivisionEtBureau',
        ),
        migrations.RenameField(
            model_name='agent',
            old_name='departement',
            new_name='Division_Bureau',
        ),
    ]
