---
description: "Le contrôle JSON-LD trouve les erreurs de structure"
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Vérifie mon JSON-LD :
{"@context":"https://schema.org","@graph":[
 {"@type":"WebPage","@id":"https://exemple.com/plomberie/#webpage","url":"https://exemple.com/plomberie/","name":"Plomberie"},
 {"@type":"WebPage","@id":"https://exemple.com/plomberie/","url":"https://exemple.com/plomberie/","name":"Plomberie bis"},
 {"@type":"BreadcrumbList","itemListElement":[
   {"@type":"ListItem","position":1,"name":"Accueil","item":"https://exemple.com/"},
   {"@type":"ListItem","position":3,"name":"Plomberie","item":"https://exemple.com/plomberie/"}]}]}
