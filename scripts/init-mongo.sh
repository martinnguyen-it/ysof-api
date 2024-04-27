mongosh -- "$MONGODB_DATABASE" <<EOF
    var rootUser = '$MONGODB_USERNAME';
    var rootPassword = '$MONGODB_PASSWORD';
    var admin = db.getSiblingDB('admin');
    admin.auth(rootUser, rootPassword);

    var user = '$MONGODB_USERNAME';
    var passwd = '$MONGODB_PASSWORD';

    db.createUser({user: user, pwd: passwd, roles: ["readWrite", "dbAdmin"]});
    use $MONGODB_DATABASE;
    db.auth(user, passwd);
    db.Admins.insertOne({
        "_cls": "AdminModel",
        "email": "ysofweb21@gmail.com",
        "status": "active",
        "roles": ["admin"],
        "holy_name": "YSOF",
        "full_name": "Admin",
        "password": "\$2b\$12\$bFmH3NeboT6MMMVnFEKxmOUJwDtwxTARykY5bjZLpvQU1M1E1qnhu",
        "created_at": new Date(),
        "updated_at": new Date(),
        "current_season": 1,
        "seasons": [1]
    });
EOF
