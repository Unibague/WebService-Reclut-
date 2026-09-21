FROM php:8.3-apache

# Habilita mod_rewrite para el .htaccess
RUN a2enmod rewrite

# Permite que .htaccess funcione en el directorio raíz
RUN sed -i 's/AllowOverride None/AllowOverride All/' /etc/apache2/apache2.conf

WORKDIR /var/www/html

COPY . .

# Crea el directorio de caché con permisos de escritura para Apache
RUN mkdir -p cache && chown -R www-data:www-data cache && chmod 755 cache

# cache/ se monta como bind mount en docker-compose.yml, lo que sobrescribe
# los permisos de arriba con los del host. El entrypoint los repara en cada
# arranque del contenedor.
RUN chmod +x docker-entrypoint.sh
ENTRYPOINT ["./docker-entrypoint.sh"]

EXPOSE 80
CMD ["apache2-foreground"]
