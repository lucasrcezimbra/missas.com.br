import scrapy


class SaoPauloSpider(scrapy.Spider):
    name = "sao_paulo"
    allowed_domains = ["arquisp.org.br"]
    start_urls = [
        "https://arquisp.org.br/regiao-belem/",
        "https://arquisp.org.br/regiao-brasilandia/",
        "https://arquisp.org.br/regiao-ipiranga/",
        "https://arquisp.org.br/regiao-lapa/",
        "https://arquisp.org.br/regiao-santana/",
        "https://arquisp.org.br/regiao-se/",
    ]

    def parse(self, response):
        """Parse regional pages to extract parish links."""
        parish_links = response.css('a[href*="/paroquia-"]::attr(href)').getall()

        self.logger.info(f"Found {len(parish_links)} parish links on {response.url}")

        for link in parish_links:
            if link:
                absolute_url = response.urljoin(link)
                if "arquisp.org.br" in absolute_url:
                    yield response.follow(link, self.parse_parish)
                else:
                    self.logger.warning(f"Skipping invalid link: {link}")

    def parse_parish(self, response):
        """Parse individual parish page to extract all information."""
        parish_name = response.css("h1.entry-title::text").get()

        if not parish_name:
            parish_name = response.css("title::text").get()
            if parish_name and " - " in parish_name:
                parish_name = parish_name.split(" - ")[0].strip()

        all_text = response.css("body ::text").getall()
        page_text = " ".join(all_text)

        phone_numbers = self._extract_all_phones(page_text)
        phone = phone_numbers[0] if phone_numbers else None
        phone2 = phone_numbers[1] if len(phone_numbers) > 1 else None

        email = None
        email_links = response.css('a[href^="mailto:"]::attr(href)').getall()
        if email_links:
            email = email_links[0].replace("mailto:", "")

        facebook = None
        instagram = None
        whatsapp = None

        for link in response.css("a::attr(href)").getall():
            if "facebook.com" in link:
                username = self._extract_facebook_username(link)
                if username and username != "arquisp":
                    facebook = username
            elif "instagram.com" in link:
                username = self._extract_instagram_username(link)
                if username and username != "arquisp":
                    instagram = username
            elif "wa.me" in link or "whatsapp" in link.lower():
                whatsapp = self._extract_whatsapp_from_url(link)

        address = None
        for h3 in response.css("h3"):
            h3_text = "".join(h3.css("::text").getall()).lower()
            if "endereço" in h3_text or "localização" in h3_text:
                next_elements = h3.xpath("following-sibling::*[position()<=2]")
                address_text = " ".join(next_elements.css("::text").getall()).strip()
                if address_text:
                    import re

                    address_text = re.sub(
                        r"\s*(Contato|Data de Fundação|Pároco).*$",
                        "",
                        address_text,
                        flags=re.IGNORECASE,
                    )
                    address = address_text.strip()
                    break

        if not address:
            import re

            for text in all_text:
                if re.search(r"(?:rua|avenida|av\.|largo|praça)\s+", text.lower()):
                    if len(text.strip()) > 10 and len(text.strip()) < 200:
                        address = text.strip()
                        break

        parish_priest = None
        for h3 in response.css("h3"):
            h3_text = "".join(h3.css("::text").getall()).lower()
            if "pároco" in h3_text or "vigário" in h3_text:
                next_elements = h3.xpath("following-sibling::*[position()<=2]")
                priest_text = " ".join(next_elements.css("::text").getall()).strip()
                if priest_text:
                    import re

                    priest_text = re.sub(
                        r"\s*(Data de Fundação|Contato|Endereço).*$",
                        "",
                        priest_text,
                        flags=re.IGNORECASE,
                    )
                    parish_priest = priest_text.strip()
                    break

        mass_schedule = []
        confession_schedule = []

        for h3 in response.css("h3"):
            h3_text = "".join(h3.css("::text").getall()).lower().strip()

            if "missa" in h3_text and "missa" == h3_text[:5]:
                next_elements = h3.xpath("following-sibling::*[position()<=10]")
                schedule_lines = []
                for elem in next_elements:
                    elem_text = " ".join(elem.css("::text").getall()).strip()
                    if elem_text and len(elem_text) > 3:
                        if any(
                            keyword in elem_text.lower()
                            for keyword in [
                                "confissão",
                                "contato",
                                "endereço",
                                "pároco",
                            ]
                        ):
                            break
                        schedule_lines.append(elem_text)
                if schedule_lines:
                    mass_schedule = schedule_lines
            elif "confissão" in h3_text or "confissões" in h3_text:
                next_elements = h3.xpath("following-sibling::*[position()<=10]")
                schedule_lines = []
                for elem in next_elements:
                    elem_text = " ".join(elem.css("::text").getall()).strip()
                    if elem_text and len(elem_text) > 3:
                        if any(
                            keyword in elem_text.lower()
                            for keyword in ["contato", "endereço", "pároco", "missa"]
                        ):
                            break
                        schedule_lines.append(elem_text)
                if schedule_lines:
                    confession_schedule = schedule_lines

        yield {
            "parish_name": parish_name,
            "state": "São Paulo",
            "city": "São Paulo",
            "phone": phone,
            "phone2": phone2,
            "email": email,
            "facebook": facebook,
            "instagram": instagram,
            "whatsapp": whatsapp,
            "address": address,
            "parish_priest": parish_priest,
            "mass_schedule": " | ".join(mass_schedule) if mass_schedule else None,
            "confession_schedule": " | ".join(confession_schedule) if confession_schedule else None,
            "url": response.url,
        }

    def _extract_all_phones(self, text):
        """Extract all phone numbers from text."""
        import re

        phone_pattern = r"\(?\d{2}\)?\s*\d{4,5}[-\s]?\d{4}"
        phone_matches = re.findall(phone_pattern, text)

        phones = []
        for match in phone_matches:
            phone = re.sub(r"[^\d]", "", match)
            if len(phone) >= 10 and phone not in [p.replace("+55", "") for p in phones]:
                phones.append(f"+55{phone}")

        return phones

    def _extract_facebook_username(self, url):
        """Extract Facebook username from URL."""
        import re

        match = re.search(r"facebook\.com/([^/?\s]+)", url)
        if match:
            username = match.group(1)
            if username not in ["pages", "profile.php"]:
                return username
        return None

    def _extract_instagram_username(self, url):
        """Extract Instagram username from URL."""
        import re

        match = re.search(r"instagram\.com/([^/?\s]+)", url)
        if match:
            return match.group(1)
        return None

    def _extract_whatsapp_from_url(self, url):
        """Extract WhatsApp number from URL."""
        import re

        match = re.search(r"(?:wa\.me/|whatsapp.*?)(\d{12,15})", url)
        if match:
            return f"+{match.group(1)}"
        return None
