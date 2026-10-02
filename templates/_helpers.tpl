{{- define "hashicorp-snapshot.openshift" -}}
{{- if .Capabilities.APIVersions.Has "route.openshift.io/v1" }}true{{ end -}}
{{- end -}}

{{- define "hashicorp-snapshot.registry" -}}
image-registry.openshift-image-registry.svc:5000/{{ .Release.Namespace }}
{{- end -}}

{{- define "hashicorp-snapshot.host" -}}
{{- if .Values.host -}}
{{ .Values.host }}
{{- else -}}
{{- $ingress := lookup "config.openshift.io/v1" "Ingress" "" "cluster" -}}
{{ printf "%s-%s.%s" .Values.appName .Release.Namespace (dig "spec" "domain" "" $ingress) }}
{{- end -}}
{{- end -}}
