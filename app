
server {
    listen	    80;
    server_name     router2.mimas.ac.uk;

    client_max_body_size 1024M;
    proxy_read_timeout 600s;

    location / {
        proxy_pass http://localhost:5000;
        proxy_redirect off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        #proxy_buffering off;
    }
}

