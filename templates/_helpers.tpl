{{- define "hashicorp-healthcheck.openshift" -}}
{{- if .Capabilities.APIVersions.Has "route.openshift.io/v1" }}true{{ end -}}
{{- end -}}

{{- define "hashicorp-healthcheck.builds" -}}
{{- if .Capabilities.APIVersions.Has "build.openshift.io/v1" }}true{{ end -}}
{{- end -}}

{{- define "hashicorp-healthcheck.registry" -}}
image-registry.openshift-image-registry.svc:5000/{{ .Release.Namespace }}
{{- end -}}

{{- define "hashicorp-healthcheck.host" -}}
{{- if .Values.host -}}
{{ .Values.host }}
{{- else -}}
{{- $ingress := lookup "config.openshift.io/v1" "Ingress" "" "cluster" -}}
{{ printf "%s-%s.%s" .Values.appName .Release.Namespace (dig "spec" "domain" "" $ingress) }}
{{- end -}}
{{- end -}}
