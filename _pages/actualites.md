---
layout: posts
title: "Actualités"
permalink: /actualites/
# collection: actualites
entries_layout: grid
classes: wide
sort_by: date
sort_order: reverse
---

{% if site.posts.size == 0 %}

<div class="notice--info" markdown="1">
**Première actualité à venir prochainement**

Cette section contiendra :

- Les annonces de événements
- Les synthèses de contributions citoyennes
- Les mises à jour du programme
- Les jalons de la campagne

En attendant, vous pouvez :

- [Consulter le programme]({{ "/programme/" | relative_url }})
- [Contribuer dès maintenant]({{ "/contribuer/" | relative_url }})
- [Nous contacter]({{ "/contact/" | relative_url }})
</div>
{% endif %}
