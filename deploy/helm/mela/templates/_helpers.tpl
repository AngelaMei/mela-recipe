{{- define "mela.labels" -}}
app.kubernetes.io/part-of: mela
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Values.image.tag | default .Chart.AppVersion | quote }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end }}

{{- define "mela.image" -}}
{{- $root := index . 0 -}}{{- $name := index . 1 -}}
{{- $tag := required "image.tag is required (deploy.sh sets it to the git commit)" $root.Values.image.tag -}}
{{- if $root.Values.image.registry -}}
{{ printf "%s/%s:%s" (trimSuffix "/" $root.Values.image.registry) $name $tag }}
{{- else -}}
{{ printf "%s:%s" $name $tag }}
{{- end -}}
{{- end }}

{{- define "mela.pullSecrets" -}}
{{- with .Values.imagePullSecrets }}
imagePullSecrets:
{{- range . }}
  - name: {{ . }}
{{- end }}
{{- end }}
{{- end }}
