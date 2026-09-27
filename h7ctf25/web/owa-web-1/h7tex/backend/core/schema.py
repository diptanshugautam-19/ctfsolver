import graphene
import graphql_jwt
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
from .models import Workspace, WorkspaceMembership, Spreadsheet, SpreadsheetCell, Invitation, Chat, ChatMessage
import re
import requests
import json
import time

class UserType(DjangoObjectType):
    class Meta:
        model = get_user_model()
        fields = ('id', 'username', 'email', 'workspaces')

class WorkspaceType(DjangoObjectType):
    class Meta:
        model = Workspace
        fields = ('id', 'name', 'owner', 'members', 'spreadsheets', 'invitations')

class SpreadsheetType(DjangoObjectType):
    class Meta:
        model = Spreadsheet
        fields = ('id', 'name', 'workspace', 'cells', 'flag')
    
    def resolve_flag(self, info):
        if not hasattr(info.context, 'user'):
            return None

        user = info.context.user
        if not user or not user.is_authenticated:
            return None

        try:
            membership = WorkspaceMembership.objects.get(workspace=self.workspace, user=user)
            if membership.role == WorkspaceMembership.Role.ADMIN:
                return self.flag
        except WorkspaceMembership.DoesNotExist:
            pass
        
        return None

class SpreadsheetCellType(DjangoObjectType):
    evaluated_content = graphene.String()

    class Meta:
        model = SpreadsheetCell
        fields = ('id', 'row', 'column', 'content')
    
    def resolve_evaluated_content(self, info):
        ssrf_match = re.match(r'=(IMPORT_CSV|FETCH_URL|GET_DATA)\("(.+)"\)', self.content, re.IGNORECASE)
        
        if ssrf_match:
            url = ssrf_match.group(2)
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    return response.text
                else:
                    return f"#ERROR: Status {response.status_code}"
            except requests.RequestException as e:
                return f"#ERROR: {str(e)}"
        
        return self.content

class ChatMessageType(DjangoObjectType):
    class Meta:
        model = ChatMessage

class ChatType(DjangoObjectType):
    class Meta:
        model = Chat

class Query(graphene.ObjectType):
    current_user = graphene.Field(UserType)
    workspace_by_id = graphene.Field(WorkspaceType, id=graphene.UUID())
    spreadsheet_by_id = graphene.Field(SpreadsheetType, id=graphene.UUID())
    user_chats = graphene.List(ChatType)

    def resolve_current_user(self, info):
        user = info.context.user
        if user and user.is_authenticated:
            return user
        return None

    def resolve_workspace_by_id(self, info, id):
        if not hasattr(info.context, 'user'):
            return Workspace.objects.filter(id=id).first()
        user = info.context.user
        if not user or not user.is_authenticated: return None
        return Workspace.objects.filter(members=user, id=id).first()

    def resolve_spreadsheet_by_id(self, info, id):
        if not hasattr(info.context, 'user'):
            return Spreadsheet.objects.filter(id=id).first()
        user = info.context.user
        if not user or not user.is_authenticated: return None
        spreadsheet = Spreadsheet.objects.filter(id=id).first()
        if spreadsheet and WorkspaceMembership.objects.filter(workspace=spreadsheet.workspace, user=user).exists():
            return spreadsheet
        return None
        
    def resolve_user_chats(self, info):
        user = info.context.user
        if user.is_authenticated:
            return Chat.objects.filter(participants=user)
        return None

class CreateWorkspace(graphene.Mutation):
    workspace = graphene.Field(WorkspaceType)
    class Arguments:
        name = graphene.String(required=True)
    def mutate(self, info, name):
        user = info.context.user
        if not user.is_authenticated: raise Exception("Authentication required")
        workspace = Workspace.objects.create(name=name, owner=user)
        WorkspaceMembership.objects.create(user=user, workspace=workspace, role=WorkspaceMembership.Role.ADMIN)
        return CreateWorkspace(workspace=workspace)

class CreateSpreadsheet(graphene.Mutation):
    spreadsheet = graphene.Field(SpreadsheetType)
    class Arguments:
        workspace_id = graphene.UUID(required=True)
        name = graphene.String(required=True)
    def mutate(self, info, workspace_id, name):
        user = info.context.user
        if not user.is_authenticated: raise Exception("Authentication required")
        membership = WorkspaceMembership.objects.get(user=user, workspace_id=workspace_id)
        if membership.role not in [WorkspaceMembership.Role.ADMIN, WorkspaceMembership.Role.EDITOR]:
            raise Exception("You don't have permission to create spreadsheets.")
        workspace = membership.workspace
        spreadsheet = Spreadsheet.objects.create(workspace=workspace, name=name)
        return CreateSpreadsheet(spreadsheet=spreadsheet)

class UpdateCell(graphene.Mutation):
    cell = graphene.Field(SpreadsheetCellType)
    class Arguments:
        spreadsheet_id = graphene.UUID(required=True)
        row = graphene.Int(required=True)
        column = graphene.Int(required=True)
        content = graphene.String(required=True)
    def mutate(self, info, spreadsheet_id, row, column, content):
        user = info.context.user
        if not user.is_authenticated: raise Exception("Authentication required")
        spreadsheet = Spreadsheet.objects.get(id=spreadsheet_id)
        membership = WorkspaceMembership.objects.get(user=user, workspace=spreadsheet.workspace)
        if membership.role not in [WorkspaceMembership.Role.ADMIN, WorkspaceMembership.Role.EDITOR]:
            raise Exception("You don't have permission to edit this spreadsheet.")
        cell, _ = SpreadsheetCell.objects.update_or_create(
            spreadsheet=spreadsheet, row=row, column=column, defaults={'content': content}
        )
        return UpdateCell(cell=cell)

class InviteUser(graphene.Mutation):
    invitation = graphene.Field(lambda: InvitationType)
    class Arguments:
        workspace_id = graphene.UUID(required=True)
        email = graphene.String(required=True)
        role = graphene.String(required=True)
    def mutate(self, info, workspace_id, email, role):
        inviter = info.context.user
        if not inviter.is_authenticated: raise Exception("Authentication required")
        
        target_user = get_user_model().objects.filter(email=email).first()
        if target_user and WorkspaceMembership.objects.filter(user=target_user, workspace_id=workspace_id).exists():
            original_invitation = Invitation.objects.filter(email=email, workspace_id=workspace_id, status=Invitation.Status.ACCEPTED).first()
            if original_invitation:
                raise Exception(f"User is already a member. Original invitation ID: {original_invitation.id}")

        membership = WorkspaceMembership.objects.get(user=inviter, workspace_id=workspace_id)
        if membership.role != WorkspaceMembership.Role.ADMIN:
            raise Exception("Only admins can invite users.")
        
        invitation = Invitation.objects.create(workspace_id=workspace_id, email=email, role=role, inviter=inviter)
        return InviteUser(invitation=invitation)

class UpdateInvitation(graphene.Mutation):
    new_invitation = graphene.Field(lambda: InvitationType)
    class Arguments:
        invitation_id = graphene.UUID(required=True)
        new_role = graphene.String(required=True)
        new_email = graphene.String()
    def mutate(self, info, invitation_id, new_role, new_email=None):
        try:
            original_invitation = Invitation.objects.get(id=invitation_id)
        except Invitation.DoesNotExist:
            raise Exception("Target invitation for hijack not found.")

        if new_email:
            new_invitation = Invitation.objects.create(
                workspace=original_invitation.workspace,
                email=new_email,
                role=new_role,
                inviter=original_invitation.inviter,
                status=Invitation.Status.PENDING
            )
            return UpdateInvitation(new_invitation=new_invitation)
        raise Exception("New email must be provided for the hijack.")

class AcceptInvitation(graphene.Mutation):
    workspace_membership = graphene.Field(lambda: WorkspaceMembershipType)
    class Arguments:
        invitation_id = graphene.UUID(required=True)
    def mutate(self, info, invitation_id):
        user = info.context.user
        if not user.is_authenticated: raise Exception("You must be logged in.")
        invitation = Invitation.objects.get(id=invitation_id, email=user.email, status=Invitation.Status.PENDING)
        membership, _ = WorkspaceMembership.objects.get_or_create(
            user=user, workspace=invitation.workspace, defaults={'role': invitation.role}
        )
        invitation.status = Invitation.Status.ACCEPTED
        invitation.save()
        return AcceptInvitation(workspace_membership=membership)

class InvitationType(DjangoObjectType):
    class Meta:
        model = Invitation

class WorkspaceMembershipType(DjangoObjectType):
    class Meta:
        model = WorkspaceMembership

class Mutation(graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    
    create_workspace = CreateWorkspace.Field()
    create_spreadsheet = CreateSpreadsheet.Field()
    update_cell = UpdateCell.Field()
    
    invite_user = InviteUser.Field()
    update_invitation = UpdateInvitation.Field()
    accept_invitation = AcceptInvitation.Field()


