{{/*
Expand the name of the chart.
*/}}
{{- define "audit-service.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "audit-service.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "audit-service.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "audit-service.labels" -}}
helm.sh/chart: {{ include "audit-service.chart" . }}
{{ include "audit-service.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "audit-service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "audit-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "audit-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "audit-service.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the backend deployment
*/}}
{{- define "audit-service.backend.name" -}}
{{- printf "%s-backend" (include "audit-service.fullname" .) }}
{{- end }}

{{/*
Create the name of the frontend deployment
*/}}
{{- define "audit-service.frontend.name" -}}
{{- printf "%s-frontend" (include "audit-service.fullname" .) }}
{{- end }}

{{/*
Create the name of the worker deployment
*/}}
{{- define "audit-service.worker.name" -}}
{{- printf "%s-worker" (include "audit-service.fullname" .) }}
{{- end }}

{{/*
Create the name of the backend service
*/}}
{{- define "audit-service.backend.serviceName" -}}
{{- printf "%s-backend" (include "audit-service.fullname" .) }}
{{- end }}

{{/*
Create the name of the frontend service
*/}}
{{- define "audit-service.frontend.serviceName" -}}
{{- printf "%s-frontend" (include "audit-service.fullname" .) }}
{{- end }}

{{/*
Create the name of the configmap
*/}}
{{- define "audit-service.configmapName" -}}
{{- printf "%s-config" (include "audit-service.fullname" .) }}
{{- end }}

{{/*
Create the name of the secret
*/}}
{{- define "audit-service.secretName" -}}
{{- printf "%s-secret" (include "audit-service.fullname" .) }}
{{- end }}

{{/*
Create the name of the ingress
*/}}
{{- define "audit-service.ingressName" -}}
{{- printf "%s-ingress" (include "audit-service.fullname" .) }}
{{- end }}

{{/*
Create the name of the HPA
*/}}
{{- define "audit-service.hpaName" -}}
{{- printf "%s-hpa" (include "audit-service.fullname" .) }}
{{- end }}

{{/*
Backend labels
*/}}
{{- define "audit-service.backend.labels" -}}
{{ include "audit-service.labels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{/*
Frontend labels
*/}}
{{- define "audit-service.frontend.labels" -}}
{{ include "audit-service.labels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Worker labels
*/}}
{{- define "audit-service.worker.labels" -}}
{{ include "audit-service.labels" . }}
app.kubernetes.io/component: worker
{{- end }}

{{/*
Backend selector labels
*/}}
{{- define "audit-service.backend.selectorLabels" -}}
{{ include "audit-service.selectorLabels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{/*
Frontend selector labels
*/}}
{{- define "audit-service.frontend.selectorLabels" -}}
{{ include "audit-service.selectorLabels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{/*
Worker selector labels
*/}}
{{- define "audit-service.worker.selectorLabels" -}}
{{ include "audit-service.selectorLabels" . }}
app.kubernetes.io/component: worker
{{- end }}

{{/*
Create image name
*/}}
{{- define "audit-service.image" -}}
{{- $registryName := .Values.global.imageRegistry -}}
{{- $repositoryName := .Values.image.repository -}}
{{- $tag := .Values.image.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- end -}}

{{/*
Create backend image name
*/}}
{{- define "audit-service.backend.image" -}}
{{- $registryName := .Values.global.imageRegistry -}}
{{- $repositoryName := .Values.backend.image.repository -}}
{{- $tag := .Values.backend.image.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- end -}}

{{/*
Create frontend image name
*/}}
{{- define "audit-service.frontend.image" -}}
{{- $registryName := .Values.global.imageRegistry -}}
{{- $repositoryName := .Values.frontend.image.repository -}}
{{- $tag := .Values.frontend.image.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- end -}}

{{/*
Create worker image name
*/}}
{{- define "audit-service.worker.image" -}}
{{- $registryName := .Values.global.imageRegistry -}}
{{- $repositoryName := .Values.worker.image.repository -}}
{{- $tag := .Values.worker.image.tag | toString -}}
{{- printf "%s/%s:%s" $registryName $repositoryName $tag -}}
{{- end -}}

{{/*
Create environment variables from values
*/}}
{{- define "audit-service.backend.env" -}}
{{- range $key, $value := .Values.backend.env }}
- name: {{ $key }}
  value: {{ $value | quote }}
{{- end }}
{{- end }}

{{/*
Create environment variables from values for frontend
*/}}
{{- define "audit-service.frontend.env" -}}
{{- range $key, $value := .Values.frontend.env }}
- name: {{ $key }}
  value: {{ $value | quote }}
{{- end }}
{{- end }}

{{/*
Create security context
*/}}
{{- define "audit-service.securityContext" -}}
{{- with .Values.security.podSecurityContext }}
{{- toYaml . }}
{{- end }}
{{- end }}

{{/*
Create container security context
*/}}
{{- define "audit-service.containerSecurityContext" -}}
{{- with .Values.security.containerSecurityContext }}
{{- toYaml . }}
{{- end }}
{{- end }}

{{/*
Create affinity
*/}}
{{- define "audit-service.affinity" -}}
{{- with .Values.affinity }}
{{- toYaml . }}
{{- end }}
{{- end }}

{{/*
Create tolerations
*/}}
{{- define "audit-service.tolerations" -}}
{{- with .Values.tolerations }}
{{- toYaml . }}
{{- end }}
{{- end }}

{{/*
Create node selector
*/}}
{{- define "audit-service.nodeSelector" -}}
{{- with .Values.nodeSelector }}
{{- toYaml . }}
{{- end }}
{{- end }}
