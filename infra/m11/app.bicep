param location string = resourceGroup().location
param image string
param revisionSuffix string
param environmentName string = 'mbs-rc-env'
param identityName string = 'mbs-rc-pull'
param registryName string
param tenantId string
param entraClientId string
@secure()
param entraClientSecret string

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' existing = {
  name: environmentName
}

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = {
  name: identityName
}

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: registryName
}

resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'mbs-rc-app'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      secrets: [
        {
          name: 'entra-client-secret'
          value: entraClientSecret
        }
      ]
      ingress: {
        allowInsecure: false
        external: true
        targetPort: 4173
        traffic: [
          {
            latestRevision: true
            weight: 100
          }
        ]
        transport: 'auto'
      }
      registries: [
        {
          identity: identity.id
          server: registry.properties.loginServer
        }
      ]
    }
    template: {
      revisionSuffix: revisionSuffix
      containers: [
        {
          name: 'product'
          image: image
          env: [
            { name: 'MBS_AI_ENABLED', value: '0' }
            { name: 'MBS_DEPLOYMENT_REVISION', value: revisionSuffix }
            { name: 'MBS_INVESTIGATION_BACKUP', value: '/data/backups/investigations.sqlite' }
            { name: 'MBS_SQLITE_JOURNAL_MODE', value: 'DELETE' }
            { name: 'MBS_TRUST_PLATFORM_IDENTITY', value: '1' }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: { path: '/v1/health', port: 4173, scheme: 'HTTP' }
              initialDelaySeconds: 5
              periodSeconds: 30
            }
            {
              type: 'Readiness'
              httpGet: { path: '/v1/health', port: 4173, scheme: 'HTTP' }
              initialDelaySeconds: 2
              periodSeconds: 10
            }
          ]
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          volumeMounts: [
            {
              mountPath: '/data'
              volumeName: 'investigations'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 1
        rules: [
          {
            name: 'http'
            http: { metadata: { concurrentRequests: '50' } }
          }
        ]
      }
      volumes: [
        {
          name: 'investigations'
          storageName: 'investigations'
          storageType: 'AzureFile'
        }
      ]
    }
  }
}

resource auth 'Microsoft.App/containerApps/authConfigs@2024-03-01' = {
  parent: app
  name: 'current'
  properties: {
    platform: {
      enabled: true
    }
    globalValidation: {
      unauthenticatedClientAction: 'Return401'
    }
    httpSettings: {
      requireHttps: true
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          clientId: entraClientId
          clientSecretSettingName: 'entra-client-secret'
          openIdIssuer: '${az.environment().authentication.loginEndpoint}${tenantId}/v2.0'
        }
        validation: {
          allowedAudiences: [
            entraClientId
            'api://${entraClientId}'
          ]
          defaultAuthorizationPolicy: {
            allowedApplications: [
              entraClientId
            ]
          }
        }
      }
    }
  }
}

output appName string = app.name
output fqdn string = app.properties.configuration.ingress.fqdn
output revisionName string = app.properties.latestRevisionName
