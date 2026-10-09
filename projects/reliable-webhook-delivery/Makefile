GO ?= go

.PHONY: fmt vet test race build compose-up compose-down

fmt:
	gofmt -w $$(find . -name '*.go')

vet:
	$(GO) vet ./...

test:
	$(GO) test ./...

race:
	$(GO) test -race -count=1 ./...

build:
	$(GO) build ./cmd/api ./cmd/worker ./cmd/receiver

compose-up:
	docker compose up --build -d

compose-down:
	docker compose down
