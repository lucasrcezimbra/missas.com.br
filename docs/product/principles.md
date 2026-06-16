# Product Principles

Product behavior principles for Missas.com.br.

## Principles

### Reliable worship information over feature breadth

Users come to the site to make real-world decisions about Mass and confession. Accuracy, freshness, and clear source context matter more than adding many features quickly.

Implementation should preserve verification fields, source tracking, and workflows that make schedule corrections easy to review.

### Mobile-first practical access

Many users will search while away from a desktop computer. Pages should remain fast, responsive, and easy to scan on mobile.

Implementation should prefer simple navigation, clear cards, readable times, and minimal interaction cost.

### Brazilian Catholic context is first-class

The product serves Brazilian Catholic communities. Geography, accents, parish names, time formatting, and contact formats should be handled carefully.

User-facing text should be Brazilian Portuguese, while internal technical documentation remains English.

### Low operational burden protects continuity

This is a small side project with limited maintenance capacity. Choices that reduce recurring cost, deployment complexity, and contributor setup friction are product-positive.

Implementation should avoid unnecessary services, native dependencies, and infrastructure complexity unless they solve a clear product problem.

### Privacy and respect for parish contacts

Parish contact channels are operationally useful but sensitive. The product should avoid exposing or mishandling contact data beyond its intended purpose.

Implementation should protect WhatsApp and contact information, use Django security defaults, and avoid logging sensitive data.
