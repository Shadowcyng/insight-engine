from app.db.session import SessionLocal
from app.models.user import User, Role, Permission
from app.core.security import get_password_hash

def seed_database():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "stmsinghania@gmail.com").first()
        print("User", user)
        if not user:
            new_user = User(
                email="stmsinghania@gmail.com",
                hashed_password=get_password_hash("Shadowcyng@123"),
                is_active=True
            )
            db.add(new_user)
            db.commit()
            print("Seed complete: User created.")

        # 1. Create the Permission
        perm_delete = db.query(Permission).filter(Permission.name == "uploads:delete").first()
        if not perm_delete:
            perm_delete = Permission(name="uploads:delete", description="Can delete uploaded files")
            db.add(perm_delete)
            
        perm_read = db.query(Permission).filter(Permission.name == "uploads:read").first()
        if not perm_read:
            perm_read = Permission(name="uploads:read", description="Can view uploaded files")
            db.add(perm_read)

        # 2. Create the Roles
        admin_role = db.query(Role).filter(Role.name == "Admin").first()
        if not admin_role:
            admin_role = Role(name="Admin")
            # Admin gets both
            admin_role.permissions.append(perm_delete)
            admin_role.permissions.append(perm_read)
            db.add(admin_role)
            
        user_role = db.query(Role).filter(Role.name == "Standard User").first()
        if not user_role:
            user_role = Role(name="Standard User")
            # Standard User ONLY gets read
            user_role.permissions.append(perm_read)
            db.add(user_role)

        db.commit()
        print("Database seeded with Roles and Permissions.")

        # 3. Assign to an existing test user
        # (Change this email to whatever you used to register in Swagger)
        test_email = "stmsinghania@gmail.com" 
        user = db.query(User).filter(User.email == test_email).first()
        
        if user:
            # Let's make them a Standard User first so we can watch it FAIL
            user.role_id = user_role.id
            db.commit()
            print(f"Assigned 'Standard User' role to {test_email}")
        else:
            print(f"Could not find user {test_email}. Please register them first.")

    finally:
        db.close()



if __name__ == "__main__":
    seed_database()



    #  docker-compose exec api /app/.venv/bin/alembic stamp head    
    # docker-compose exec api /app/.venv/bin/python seed_rbac.py        