---
description: "JSON-LD : pièges propres à la méthode, pas seulement la syntaxe"
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Vérifie le JSON-LD de ma page service avant mise en ligne :
{"@context":"https://schema.org","@graph":[
 {"@type":"Organization","@id":"https://www.exemple.com/#organization","name":"Exemple SARL","url":"https://www.exemple.com/",
  "aggregateRating":{"@type":"AggregateRating","ratingValue":4.9,"reviewCount":87}},
 {"@type":"WebPage","@id":"https://exemple.com/crm/#webpage","url":"https://exemple.com/crm/","name":"Intégrateur CRM",
  "about":[{"@type":"Thing","name":"CRM","sameAs":"https://www.wikidata.org/wiki/Q245926"}],
  "mentions":[{"@type":"Thing","name":"CRM","sameAs":"https://www.wikidata.org/wiki/Q245926"},
              {"@type":"SoftwareApplication","name":"Microsoft Dynamics 365"}]},
 {"@type":"BreadcrumbList","itemListElement":[
   {"@type":"ListItem","position":1,"name":"Accueil","item":"https://www.exemple.com/"},
   {"@type":"ListItem","position":3,"name":"CRM","item":"https://exemple.com/crm/"}]}]}
