import {
  createPlugin,
  createRoutableExtension,
} from '@backstage/core-plugin-api';

import { rootRouteRef } from './routes';

export const auditLogPlugin = createPlugin({
  id: 'audit-log',
  routes: {
    root: rootRouteRef,
  },
});

export const AuditLogPage = auditLogPlugin.provide(
  createRoutableExtension({
    name: 'AuditLogPage',
    component: () =>
      import('./components/AuditLogPage').then(m => m.AuditLogPage),
    mountPoint: rootRouteRef,
  }),
);