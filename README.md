### Backend Deployment
- clone the repo
- sitch to backend
- install the dependyncies
  ```
  sudo yum update -y
  sudo  yum install python3-pip -y
  sudo dnf install mariadb105-server -y
  ```
- change the rds detils in ```app.py```
## Initilize the rds databse
```
mysql -h <rds-endpoint> -u admin -p<password> < test.sql   # change your detiils
mysql -h microservices.cuk1or8kdbv9.us-east-1.rds.amazonaws.com -u admin -pCloud123 < test.sql    # this  example commnd chnage values according to  your  end
```
- change the rds details inn app.py
- create the environnmnet in server for python applicationn deploymnet
```
python3 -m venv venv
source venv/bin/activate
```
- Install requriments.txt
```
pip install -r requirements.txt
```
# crete systemd service  for  backend python
```
sudo vi /etc/systemd/system/microapp.service

```
Paste the below script and change the project paths according to your cloning path
```
[Unit]
Description=Microapp Flask Application
After=network.target

[Service]
User=root
WorkingDirectory=/root/aws-ecommerce-otp-authentication/backend
Environment="PATH=/root/aws-ecommerce-otp-authentication/backend/venv/bin"
ExecStart=/root/aws-ecommerce-otp-authentication/backend/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target

```
### Start the sytemd
```
sudo systemctl daemon-reload
sudo systemctl restart microapp
sudo systemctl status microapp
```

### Frontend Deployment

- clone the repo
- sitch to frontend
- install the dependyncies

```
sudo yum update -y
sudo  yum install nginx -y
sudo systemctl start nginx
sudo systemctl enable  nginx
```
- change the backend public in frontend index.html login and signup
```
- // === Configuration ===
-       const API_BASE = "http://54.161.16.143:5000/api"; 
```
- after this copyrhis  files to nginx path
```
sudo cp -r * /usr/share/nginx/html
```

- hit frontend public ip
```
