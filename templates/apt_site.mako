server {
server_name apt.algebra;
listen 80;
listen [::]:80;
location /debian {
alias /debian;
    autoindex on;
}

}
