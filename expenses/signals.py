from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Expense

@receiver(post_migrate)
def create_roles_and_permissions(sender, **kwargs):
    if sender.name == "expenses":
        # Create or Get Groups
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        manager_group, _ = Group.objects.get_or_create(name="Manager")
        user_group, _ = Group.objects.get_or_create(name="User")

        # Define Permissions for Expense Model
        content_type = ContentType.objects.get_for_model(Expense)
        
        permissions = {
            "Admin": ["add_expense", "change_expense", "delete_expense", "view_expense"],
            "Manager": ["add_expense", "change_expense", "view_expense"],
            "User": ["view_expense"],
        }

        # Assign Permissions to Groups
        for role, perms in permissions.items():
            group = Group.objects.get(name=role)
            for perm in perms:
                permission = Permission.objects.get(codename=perm, content_type=content_type)
                group.permissions.add(permission)

