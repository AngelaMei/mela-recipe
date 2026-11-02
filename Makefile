# Mela: common commands. Deploys go through deploy/deploy.sh (Helm).
#
#   make deploy               build from HEAD, push, roll out
#   make deploy ARGS=--skip-build
#   make render               print the manifests without changing anything

NS ?= mela

.PHONY: test deploy render status logs psql backup-now dev

test:
	cd backend && python -m pytest -q
	cd web && npm run typecheck

deploy:
	deploy/deploy.sh $(ARGS)

render:
	deploy/deploy.sh --dry-run

status:
	kubectl -n $(NS) get pods,svc,ingress,certificate,pvc

logs:
	kubectl -n $(NS) logs deploy/mela-api --all-containers --tail=100

psql:
	kubectl -n $(NS) exec -it statefulset/mela-postgres -- sh -c 'psql -U "$$POSTGRES_USER" "$$POSTGRES_DB"'

backup-now:
	kubectl -n $(NS) create job --from=cronjob/mela-backup mela-backup-manual-$$(date +%s)

dev:
	docker compose up --build
