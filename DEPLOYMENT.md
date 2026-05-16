# Deployment Guide

This project should be deployed as a hosted Frappe/ERPNext application with the custom app installed alongside ERPNext.

## Current Package

- Custom app: `apps/business_customizations`
- ERPNext branch used in development: `version-16`
- Frappe branch used in development: `version-16`
- Trial site used locally: `business.localhost`

The local Codespaces Bench is for development only. Do not use it as production hosting.

## Recommended Pilot Hosting

Use a small VPS first, then scale after field testing.

Minimum pilot server:

- Ubuntu 24.04 LTS
- 4 vCPU
- 8 GB RAM
- 80 GB SSD
- Domain name, e.g. `dms.yourdomain.com`
- Daily backups

Better production server:

- 8 vCPU
- 16 GB RAM
- 160 GB SSD
- Separate backup storage
- Monitoring and SSL

## Deployment Shape

```text
Cloud VPS
  Frappe Bench / Docker
  MariaDB
  Redis
  ERPNext version-16
  business_customizations app
  HTTPS domain
```

## Manual Bench Install Flow

Run this on the server after installing Bench prerequisites:

```bash
bench init tallspan-bench --frappe-branch version-16
cd tallspan-bench
bench get-app erpnext --branch version-16
bench get-app <business_customizations_git_url>
bench new-site dms.yourdomain.com
bench --site dms.yourdomain.com install-app erpnext
bench --site dms.yourdomain.com install-app business_customizations
bench --site dms.yourdomain.com migrate
bench setup production <linux-user>
```

Before this can run, `apps/business_customizations` should be pushed as its own Git repository or included in a custom Docker image.

## Pilot Checklist

1. Deploy fresh server.
2. Create real company, users, warehouses, trucks, and item masters.
3. Import customer and product data.
4. Test Truck Load Sheet and Stock Entry transfer.
5. Let warehouse and sales users test real workflows.
6. Collect feedback daily.
7. Iterate in `business_customizations`, then redeploy.

## Not Yet Production-Ready

The current system is ready for a technical pilot, not final production. Still needed:

- Backups and restore testing
- Email setup
- Domain and SSL
- User roles and permissions
- Opening stock and valuation
- Data imports
- Production server hardening
- M-Pesa/GPS/mobile integrations

