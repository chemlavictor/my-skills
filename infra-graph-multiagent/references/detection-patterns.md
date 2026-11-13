# Detection patterns

Starting points for each agent. They are hints, not a checklist: a repo may use none of them, and the discovery output tells you what is actually present. When a technology is not listed, apply the same reasoning (what defines machines, mounts, data stores, doors).

## Hosts
| Technology | Look for |
|---|---|
| Ansible | `inventory*`, `hosts`, `serverlist/`, `group_vars/`, `host_vars/`, `playbooks/*.yml` (`hosts:` and `roles:`), `roles/*/tasks` (what gets installed) |
| Terraform | `aws_instance`, `azurerm_*_virtual_machine`, `google_compute_instance`, `hcloud_server`, `kubernetes_*`, module sources |
| Docker Compose | `services:` keys, `image:`/`build:`, `depends_on`, `networks`, `container_name`, `hostname` |
| Kubernetes / Helm | `Deployment`, `StatefulSet`, `DaemonSet`, `CronJob`, `values*.yaml`, node selectors |
| Serverless / PaaS | `serverless.yml`, `template.yaml`, `app.yaml`, `Procfile`, `fly.toml`, `render.yaml` |
| Bare scripts | `deploy*.sh`, `provision*.sh`, `Vagrantfile`, `.service` units, CI deploy jobs with `ssh` targets |

## Storage
| Technology | Look for |
|---|---|
| Docker | top-level `volumes:`, service `volumes:` (named = managed by Docker, `./x:/y` = bind mount) |
| Kubernetes | `PersistentVolumeClaim`, `storageClassName`, `mountPath`, `hostPath`, `emptyDir` (ephemeral!) |
| Cloud | `aws_ebs_volume`, `aws_efs_file_system`, `aws_s3_bucket`, `azurerm_managed_disk`, `azurerm_storage_account`, `google_storage_bucket` |
| Ansible | tasks using `mount`, `filesystem`, `lvol`, `file` on `/var/lib`, `/data`, `/srv`, `/mnt` |
| App config | `UPLOAD_DIR`, `MEDIA_ROOT`, `STORAGE_PATH`, `LOG_DIR`, `BACKUP_DIR`, multer/`FileSystemStorage`, S3/Blob SDK clients |
| Backups | `pg_dump`, `mysqldump`, `mongodump`, `restic`, `borg`, `rsync`, `aws s3 sync`, cron/timer entries |

## Databases
| Signal | Meaning |
|---|---|
| `postgres://`, `mongodb://`, `mysql://`, `redis://`, `amqp://` | connection string; host part tells internal vs external |
| `*.rds.amazonaws.com`, `*.mongodb.net`, `*.database.azure.com`, `*.cloudsql`, `*.cache.amazonaws.com` | external managed service |
| compose/k8s image `postgres`, `mongo`, `redis`, `rabbitmq`, `elasticsearch` | internal container |
| ORM config and models | `models.py`, `*.entity.ts`, `schema.prisma`, `models/*.js`, `mongoose.Schema`, SQLAlchemy `Base`, migrations folder |
| Env var names | `DATABASE_URL`, `DB_HOST`, `MONGO_URI`, `REDIS_URL`, `ELASTICSEARCH_URL` (value may live outside repo: say so) |

## Inbound
| Door | Look for |
|---|---|
| Public ports | compose `ports:`, k8s `Service` type `LoadBalancer`/`NodePort`, security groups (`ingress`), firewall tasks (`ufw`, `iptables`, `firewalld`) |
| Reverse proxy | nginx `server`/`location`/`proxy_pass`/`upstream`, haproxy `frontend`/`backend`, traefik routers, k8s `Ingress` |
| API routes | route decorators and controllers (`@app.route`, `@Get()`, `router.post`) |
| Webhooks | handlers named `webhook`, signature verification (`X-Hub-Signature`, `Stripe-Signature`), callback URLs in config |
| Queues | consumers (`basic_consume`, `@RabbitListener`, `KafkaConsumer`, SQS/PubSub subscribers) |
| File / mail drops | SFTP/FTP server config, watched folders, IMAP/POP3 pollers, SMTP receivers |
| Scheduled pulls | cron, systemd timers, `schedule:` in CI or k8s CronJob, scripts that call partner APIs |
| Admin access | SSH users and keys in ansible, bastion hosts, CI deploy credentials (names only) |
