2026-11-19 12:41:32,005 INFO sqlalchemy.engine.Engine [generated in 0.00022s] {}
Super Admin Email: apexiveai@aol.com
Full Name: Kyawsanlinn
Password:
Confirm Password:
2026-11-19 12:41:57,245 INFO sqlalchemy.engine.Engine SELECT users.id, users.email, users.phone, users.full_name, users.password_hash, users.is_active, users.is_superuser, users.last_login_at, users.created_at, users.updated_at
FROM users
WHERE users.email = %(email_1)s::VARCHAR
2026-11-19 12:41:57,245 INFO sqlalchemy.engine.Engine [generated in 0.00053s] {'email_1': 'apexiveai@aol.com'}
2026-11-19 12:41:57,328 INFO sqlalchemy.engine.Engine INSERT INTO users (id, email, phone, full_name, password_hash, is_active, is_superuser, last_login_at) VALUES (%(id)s::UUID, %(email)s::VARCHAR, %(phone)s::VARCHAR, %(full_name)s::VARCHAR, %(password_hash)s::VARCHAR, %(is_active)s, %(is_superuser)s, %(last_login_at)s::TIMESTAMP WITH TIME ZONE) RETURNING users.created_at, users.updated_at
2026-11-19 12:41:57,328 INFO sqlalchemy.engine.Engine [generated in 0.00029s] {'id': UUID('486633f2-8e67-478c-be6c-caa6dd8e43b6'), 'email': 'apexiveai@aol.com', 'phone': None, 'full_name': 'Kyawsanlinn', 'password_hash': '$argon2id$v=19$m=65536,t=3,p=4$UizdxH1e9Tm4SBVJSGk1aQ$jb3NJ0389sTH6vejePFVKMuo7QP+7JNTkUR+5SnRGgc', 'is_active': True, 'is_superuser': True, 'last_login_at': None}
2026-11-19 12:41:57,338 INFO sqlalchemy.engine.Engine COMMIT
==================================================
SUPER ADMIN CREATED SUCCESSFULLY
Email: apexiveai@aol.com
User ID: 486633f2-8e67-478c-be6c-caa6dd8e43b6
==================================================