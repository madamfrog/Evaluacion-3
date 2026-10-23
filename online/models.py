from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, correo, usuario, password=None, **extra_fields):
        """
        Crea y guarda un usuario con el correo, usuario y password dados.
        """
        if not correo:
            raise ValueError("El usuario debe tener un correo electrónico")
        if not usuario:
            raise ValueError("El usuario debe tener un nombre de usuario")

        user = self.model(
            correo=self.normalize_email(correo), usuario=usuario, **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, correo, usuario, password=None, **extra_fields):
        """
        Crea y guarda un superusuario con el correo, usuario y password dados.
        """
        extra_fields.setdefault("admin", True)
        extra_fields.setdefault("activo", True)
        extra_fields.setdefault("tecnico", True)

        if extra_fields.get("admin") is not True:
            raise ValueError("Superuser debe tener admin=True.")

        return self.create_user(correo, usuario, password, **extra_fields)


class Usuario(AbstractBaseUser):
    nombre = models.CharField(
        verbose_name="Nombre", max_length=30, blank=True, null=True
    )
    apellido = models.CharField(
        verbose_name="Apellido", max_length=30, blank=True, null=True
    )
    rut = models.CharField(
        verbose_name="RUT", max_length=12, unique=True, blank=True, null=True
    )
    correo = models.EmailField(
        verbose_name="Correo electrónico",
        max_length=70,
        unique=True,
    )
    usuario = models.CharField(
        verbose_name="Usuario",
        max_length=50,
        unique=True,
    )
    fecha_nacimiento = models.DateField(
        verbose_name="Fecha de nacimiento", null=True, blank=True
    )
    activo = models.BooleanField(default=True)
    admin = models.BooleanField(default=False)
    tecnico = models.BooleanField(default=False)

    USERNAME_FIELD = "usuario"
    REQUIRED_FIELDS = ["correo"]

    objects = UserManager()

    def get_full_name(self):
        return f"{self.nombre} {self.apellido}"

    def get_short_name(self):
        return self.usuario

    def has_perm(self, perm, obj=None):
        return self.is_active and self.admin

    def has_module_perms(self, app_label):
        return self.is_active and self.admin

    @property
    def is_active(self):
        return self.activo

    @property
    def is_staff(self):
        return self.admin

    @property
    def is_admin(self):
        return self.admin

    def __str__(self):
        return self.usuario


class Preguntas(models.Model):
    idPregunta = models.AutoField(primary_key=True)
    Titulo = models.CharField(max_length=60)
    Pregunta = models.TextField()
    Fecha_creacion = models.DateTimeField()
    Usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.idPregunta} - {self.Titulo}"


class Respuesta(models.Model):
    idRespuesta = models.AutoField(primary_key=True)
    Respuesta = models.TextField(verbose_name="Respuesta")
    id_Pregunta = models.ForeignKey(Preguntas, on_delete=models.CASCADE)
    Usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    FechaHora = models.DateTimeField()

    def __str__(self):
        return f"{self.idRespuesta} - {self.Respuesta[:20]}"
