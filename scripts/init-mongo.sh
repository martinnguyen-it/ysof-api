mongosh -- "$MONGODB_DATABASE" <<EOF
    var rootUser = '$MONGO_INITDB_ROOT_USERNAME';
    var rootPassword = '$MONGO_INITDB_ROOT_PASSWORD';
    var admin = db.getSiblingDB('admin');
    admin.auth(rootUser, rootPassword);

    var user = '$MONGODB_USERNAME';
    var passwd = '$MONGODB_PASSWORD';

    db.createUser({user: user, pwd: passwd, roles: ["readWrite", "dbAdmin"]});
    use $MONGODB_DATABASE;
    db.auth(user, passwd);
    db.Users.insertOne({
        "_cls": "User",
        "email": "accountant@bhsoft.vn",
        "status": "active",
        "role": "accountant",
        "first_name": "bhsoft",
        "last_name": "bhsoft",
        "hashed_password": "\$2b\$12\$vOMvhYM4zx57zTCc03H4Hu6qyv/h6KnLW1bJPFEU4EMW26m9sKlOe",
        "created_at": new Date(),
        "updated_at": new Date(),
    });
EOF
