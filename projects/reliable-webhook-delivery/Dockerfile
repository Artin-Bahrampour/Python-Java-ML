FROM golang:1.27-alpine AS build
RUN apk add --no-cache ca-certificates git
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/api ./cmd/api \
 && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/worker ./cmd/worker \
 && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/receiver ./cmd/receiver

FROM gcr.io/distroless/static-debian12:nonroot AS runtime
WORKDIR /app
COPY --from=build --chown=nonroot:nonroot /out/api /app/api
COPY --from=build --chown=nonroot:nonroot /out/worker /app/worker
COPY --chown=nonroot:nonroot config/targets.json /app/config/targets.json
USER nonroot:nonroot
EXPOSE 8080 9090
CMD ["/app/api"]

# Development-only image: the production runtime does not contain the sample receiver binary.
FROM runtime AS devreceiver
COPY --from=build --chown=nonroot:nonroot /out/receiver /app/receiver
EXPOSE 8081
CMD ["/app/receiver"]
