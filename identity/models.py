from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Q
from django.conf import settings
import hashlib


class Role(models.Model):
    id = models.AutoField(primary_key=True)
    CODE_CHOICES = (
        ('limited','Limited'),
        ('regular','Regular'),
        ('editor','Editor'),
        ('admin','Admin'),
        ('super_admin','Super Admin'),
    )
    code = models.CharField(
        unique=True
        ,max_length=15
        ,choices=CODE_CHOICES
    )
    title = models.CharField(max_length=100)
    level = models.IntegerField()
    is_system = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$',)],
        unique=True,
        max_length=15
    )
    STATUS_CHOICES = (
        ('unverified','Unverified'),
        ('pending','Pending'),
        ('active','Active'),
        ('suspended','Suspended'),
        ('deleted','Deleted'),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
    )
    email_verified = models.BooleanField(default=False)
    failed_login_attempts = models.IntegerField(default=0)
    last_login_at = models.DateTimeField(null=True , blank=True)

    role = models.ForeignKey(
        'Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True,blank=True)

    def save(self , *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        if self.username:
            self.username = self.username.lower()
        super(User, self).save(*args, **kwargs)


    def __str__(self):
        return self.username


class Group(models.Model):
    id = models.AutoField(primary_key=True)

    code = models.BigIntegerField(unique=True, editable=False)

    title = models.CharField(max_length=100)

    title_normalized = models.CharField(
        max_length=100,
        unique=True,
        editable=False,
        null=True,
        blank=True
    )

    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    assigned_by = models.ForeignKey(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='groups_created_by'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.title:
            self.title_normalized = self.title.strip().lower()

            hash_value = hashlib.sha256(
                self.title_normalized.encode('utf-8')
            ).hexdigest()

            self.code = int(hash_value[:12], 16)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class UserGroup(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='user_memberships'
    )
    group = models.ForeignKey(
        'Group',
        on_delete=models.CASCADE,
        related_name='group_memberships'
    )
    assigned_by = models.ForeignKey(
        'identity.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_groups'
    )
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_groups'

        unique_together = ('user','group')

        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                condition=Q(is_primary=True),
                name='unique_primary_group_per_user'
            )
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.group.title}"

class Domain(models.Model):
    id = models.AutoField(primary_key=True)
    domain_name = models.TextField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_domains'
    )
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    group_id = models.ManyToManyField('Group')

    def __str__(self):
        return self.domain_name

class Tag(models.Model):
    id = models.AutoField(primary_key=True)
    tag_title = models.CharField(max_length=100)
    tag_title_normalized = models.CharField(
        max_length=100,
        unique=True,
        editable=False,
        null=True,
        blank=True
    )
    code = models.BigIntegerField(unique=True, editable=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_tags'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
    def save(self, *args, **kwargs):
        if self.tag_title:
            self.tag_title_normalized = self.tag_title.strip().lower()

            hash_value = hashlib.sha256(
                self.tag_title_normalized.encode('utf-8')
            ).hexdigest()

            self.code = int(hash_value[:12], 16)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.tag_title

class User_Domain_Tag(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
    )
    domain = models.ForeignKey(
        'Domain',
        on_delete=models.CASCADE,
    )
    tag = models.ForeignKey(
        'Tag',
        on_delete=models.CASCADE,
    )
    class Meta:
        constraints = [
            # combine of user & domain should be unique
            models.UniqueConstraint(fields=['user','domain'], name='unique_user_tag_per_domain')
        ]
    def __str__(self):
        return f"{self.user} - {self.domain} - {self.tag}"
