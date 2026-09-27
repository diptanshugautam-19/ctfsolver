import os
import django
import secrets
import uuid
from django.utils import timezone
import datetime

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ctf_challenge.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import Workspace, WorkspaceMembership, Spreadsheet, SpreadsheetCell, Invitation, Chat, ChatMessage

User = get_user_model()

def run():
    print("Seeding CTF data with new narrative...")

    # 1. Create the challenger's user account
    challenger, created_challenger = User.objects.get_or_create(
        username="gotret",
        defaults={'email': 'gotret@synchgrid.com'}
    )
    if created_challenger:
        challenger.set_password("getrek")
        challenger.save()
        print(f"Created challenger account: {challenger.username}")

    # 2. Create the Manager user
    manager, created_manager = User.objects.get_or_create(
        username="h7tex-dev",
        defaults={'email': 'h7tex-dev@synchgrid.com'}
    )
    if created_manager:
        manager.set_password("#$%^&&*DFfdfvcoowwe")
        manager.save()
        print(f"Created manager account: {manager.username}")
    
    # 3. Create the Intern user
    intern, created_intern = User.objects.get_or_create(
        username="cookie",
        defaults={'email': 'cookie@synchgrid.com'}
    )
    if created_intern:
        intern.set_password("PWER$#*&^kc")
        intern.save()
        print(f"Created intern account: {intern.username}")

    # 4. Create the target workspace
    synchgrid_workspace, created_ws = Workspace.objects.get_or_create(
        name="synchgrid",
        defaults={'owner': manager}
    )
    if created_ws:
        print(f"Created target workspace: {synchgrid_workspace.name} (ID: {synchgrid_workspace.id})")

    # 5. Add Manager and Intern as members of the 'synchgrid' workspace
    WorkspaceMembership.objects.get_or_create(
        user=manager,
        workspace=synchgrid_workspace,
        defaults={'role': WorkspaceMembership.Role.ADMIN}
    )
    WorkspaceMembership.objects.get_or_create(
        user=intern,
        workspace=synchgrid_workspace,
        defaults={'role': WorkspaceMembership.Role.VIEWER}
    )
    print("Added members to 'synchgrid' workspace.")

    # 6. Create an ACCEPTED invitation for the intern (to make the leak possible)
    Invitation.objects.get_or_create(
        email=intern.email,
        workspace=synchgrid_workspace,
        status=Invitation.Status.ACCEPTED,
        defaults={'role': WorkspaceMembership.Role.VIEWER, 'inviter': manager}
    )
    print(f"Created accepted invitation for {intern.email} to enable leak.")
   
   
   
    # --- DYNAMIC FLAG GENERATION ---
    # 1. Get the flag format from the environment variable.
    flag_format = os.environ.get('FLAG_FORMAT', 'H7Tex{%s_fallback}')
    
    # 2. Generate a 16-character random hex string for the unique part.
    random_part = secrets.token_hex(8)
    
    # 3. Construct the final, unique flag for this instance.
    the_flag = flag_format % random_part
    
    print(f"Generated dynamic flag for this instance: {the_flag}")

    # 4. Create the target spreadsheet with the dynamic flag.
    financials_sheet, _ = Spreadsheet.objects.update_or_create(
        workspace=synchgrid_workspace,
        name="Financials Q4",
        defaults={'flag': the_flag}
    )
    SpreadsheetCell.objects.update_or_create(
        spreadsheet=financials_sheet, 
        row=31, 
        column=5, 
        defaults={'content': the_flag}
    )
    
    
    # 7. Create the target spreadsheet
    financials_sheet, _ = Spreadsheet.objects.get_or_create(
        workspace=synchgrid_workspace,
        name="Financials Q4",
        defaults={'flag': 'H7Tex{t3n4nt_h0pp1ng_v1a_l34ky_4p1s}'}
    )
    SpreadsheetCell.objects.get_or_create(
        spreadsheet=financials_sheet, 
        row=17, 
        column=5, 
        defaults={'content': 'H7Tex{t3n4nt_h0pp1ng_v1a_l34ky_4p1s}'}
    )
    print(f"Created target spreadsheet: {financials_sheet.name}")

    # 8. Create the challenger's personal workspace
    challenger_ws, _ = Workspace.objects.get_or_create(
        name=f"{challenger.username}'s Personal Space",
        owner=challenger
    )
    WorkspaceMembership.objects.get_or_create(
        user=challenger,
        workspace=challenger_ws,
        defaults={'role': WorkspaceMembership.Role.ADMIN}
    )
    print(f"Created personal workspace for {challenger.username}")

    # 9. Create the chat conversation with clues
    chat, created_chat = Chat.objects.get_or_create()
    if created_chat:
        chat.participants.add(challenger, manager)
        
        # Message 1 (from manager)
        ChatMessage.objects.create(
        chat=chat,
        sender=manager,
        content="Hi gotret. Afraid I have some bad news - your request for access to the 'synchgrid' production workspace couldn't be approved following the latest security compliance review. We can revisit this next quarter.",
        timestamp=timezone.now() - datetime.timedelta(minutes=10)
    )
    ChatMessage.objects.create(
        chat=chat,
        sender=manager,
        content="On a related note, I've just onboarded our new intern, cookie@synchgrid.com. I've given him viewer access to the 'Financials Q4' sheet so he can get up to speed. He passed all his checks, so it's all good.",
        timestamp=timezone.now() - datetime.timedelta(minutes=9)
    )
    ChatMessage.objects.create(
        chat=chat,
        sender=manager,
        content="By the way, I saw a note from the dev team about the spreadsheet formula processor. Apparently, they temporarily hooked it up directly to the internal-graphql gateway which is on port 8000 for testing some CSV function. They need to remember to remove that before the production push, it completely bypasses our normal security checks.",
        timestamp=timezone.now() - datetime.timedelta(minutes=8)
    )
    print("Created polished chat conversation with contextual clues.")

    print("\nCTF data seeding complete!")
    print(f"Challenger Login -> username: {challenger.username}, password: getrek")

if __name__ == '__main__':
    run()


