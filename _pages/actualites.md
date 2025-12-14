---
layout: collection
title: "Actualités"
permalink: /actualites/
collection: actualites
entries_layout: grid
sort_by: date
sort_order: reverse
---

Suivez l'évolution de la campagne, les nouvelles contributions au programme, et les événements à venir.

{% if site.actualites.size == 0 %}
<div class="notice--info" markdown="1">
**Première actualité à venir prochainement**

Cette section contiendra :
- Les annonces de permanences et événements
- Les synthèses de contributions citoyennes
- Les mises à jour du programme
- Les jalons de la campagne

En attendant, vous pouvez :
- [Consulter le programme]({{ "/programme/" | relative_url }})
- [Contribuer dès maintenant]({{ "/contribuer/" | relative_url }})
- [Nous contacter]({{ "/contact/" | relative_url }})
</div>
{% endif %}
