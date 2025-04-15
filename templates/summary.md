# {{ MainTitle }}

<div style="background-color: #053345; padding: 8px 15px; border-radius: 20px; display: inline-block;">Total Word Count: {{ count }}</div>
<div style="color: #7f8c8d; font-size: 14px;">Paragraphs: {{ paragraphs }}</div>

---

## {{ subtitle1 }}

{{ content1 }}

## {{ subtitle2 }}

{{ content2 }}

## {{ subtitle3 }}

{{ content3 }}

## {{ subtitle4 }}

<div style="background-color: #053345; padding: 20px; border-radius: 6px; border-left: 4px solid #3498db;">

{% for finding in findings %}
- {{ finding }}
{% endfor %}

</div>

## {{ subtitle5 }}

<div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px;">
{% for term in terms %}
<span style="background-color: #e9f2fd; padding: 6px 12px; border-radius: 15px; font-size: 14px; color: #2980b9;">{{ term }}</span>
{% endfor %}
</div>

## {{ subtitle6 }}

<div style="color: black;background-color: #053345; padding: 15px; border-radius: 6px;">

{% for ref in references %}
{{ loop.index }}. {{ ref.text }} [Link]({{ ref.link }})
{% endfor %}

</div>