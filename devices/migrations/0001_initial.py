# Generated by Django 3.2.7 on 2021-09-29 16:16

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AudibleDevice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_modified', models.DateTimeField(auto_now=True)),
                ('country_code', models.CharField(max_length=5)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audible_devices', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BearerToken',
            fields=[
                ('device', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='bearer', serialize=False, to='devices.audibledevice')),
                ('access_token', models.TextField(max_length=500, validators=[django.core.validators.RegexValidator(regex='^Atna\\|.*$'), django.core.validators.MaxLengthValidator(500)])),
                ('access_token_expires', models.DateTimeField()),
                ('refresh_token', models.TextField(max_length=500, validators=[django.core.validators.RegexValidator(regex='^Atnr\\|.*$'), django.core.validators.MaxLengthValidator(500)])),
            ],
        ),
        migrations.CreateModel(
            name='CustomerInfo',
            fields=[
                ('device', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='customer_info', serialize=False, to='devices.audibledevice')),
                ('account_pool', models.CharField(max_length=20)),
                ('user_id', models.CharField(max_length=100)),
                ('home_region', models.CharField(max_length=10)),
                ('name', models.CharField(max_length=50)),
                ('given_name', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='DeviceInfo',
            fields=[
                ('device', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='device_info', serialize=False, to='devices.audibledevice')),
                ('device_name', models.CharField(max_length=100)),
                ('device_serial_number', models.CharField(max_length=50)),
                ('device_type', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='MessageAuthenticationCode',
            fields=[
                ('device', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='mac_dms', serialize=False, to='devices.audibledevice')),
                ('adp_token', models.TextField(max_length=1800, validators=[django.core.validators.RegexValidator(regex='^{enc:.*}{key:.*}{iv:.*}{name:.*}{serial:Mg==}$'), django.core.validators.MaxLengthValidator(1800)])),
                ('device_cert', models.TextField(max_length=2000)),
            ],
        ),
        migrations.CreateModel(
            name='StoreAuthenticationCookie',
            fields=[
                ('device', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='store_cookie', serialize=False, to='devices.audibledevice')),
                ('cookie', models.TextField(max_length=300, validators=[django.core.validators.MaxLengthValidator(300)])),
            ],
        ),
        migrations.CreateModel(
            name='WebsiteCookie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('country_code', models.CharField(max_length=5)),
                ('name', models.CharField(max_length=30)),
                ('value', models.TextField()),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='website_cookies', to='devices.audibledevice')),
            ],
        ),
    ]