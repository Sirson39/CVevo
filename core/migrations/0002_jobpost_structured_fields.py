from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobpost",
            name="key_responsibilities",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="jobpost",
            name="preferred_skills",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="jobpost",
            name="required_skills",
            field=models.TextField(blank=True),
        ),
    ]
