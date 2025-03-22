
#!/usr/bin/bash

sudo systemctl daemon-reload
sudo rm -f /etc/nginx/sites-enabled/default

sudo cp /home/ubuntu/Devops_proj/nginx/nginx.conf /etc/nginx/sites-available/Devops_proj
sudo ln -s /etc/nginx/sites-available/Devops_proj /etc/nginx/sites-enabled/
#sudo ln -s /etc/nginx/sites-available/recipes /etc/nginx/sites-enabled
#sudo nginx -t
sudo gpasswd -a www-data ubuntu
sudo systemctl restart nginx

