// Confirmacion antes de acciones destructivas (formularios con data-confirmar)
document.addEventListener("submit", function (evento) {
  const form = evento.target;
  const mensaje = form.getAttribute("data-confirmar");
  if (mensaje && !window.confirm(mensaje)) {
    evento.preventDefault();
  }
});

// Autocompletar el precio unitario al elegir un repuesto en la orden de servicio
document.addEventListener("DOMContentLoaded", function () {
  const selectRepuesto = document.getElementById("select-repuesto");
  const inputPrecio = document.getElementById("precio-repuesto-preview");

  if (selectRepuesto && inputPrecio) {
    const actualizarPrecio = function () {
      const opcion = selectRepuesto.options[selectRepuesto.selectedIndex];
      const precio = opcion ? opcion.getAttribute("data-precio") : null;
      inputPrecio.textContent = precio ? `Precio unitario: $${Number(precio).toLocaleString("es-CO")}` : "";
    };
    selectRepuesto.addEventListener("change", actualizarPrecio);
    actualizarPrecio();
  }

  // Cierra automaticamente los mensajes flash despues de unos segundos
  document.querySelectorAll(".flash").forEach(function (el) {
    setTimeout(function () {
      el.style.transition = "opacity 0.4s ease";
      el.style.opacity = "0";
      setTimeout(function () {
        el.remove();
      }, 400);
    }, 6000);
  });

  // Menú lateral móvil
  const btnMenuMovil = document.getElementById("btn-menu-movil");
  const sidebar = document.getElementById("sidebar-principal");
  const overlay = document.getElementById("overlay-menu");

  if (btnMenuMovil && sidebar && overlay) {
    const abrirCerrarMenu = function () {
      const abierto = sidebar.classList.toggle("abierto");
      overlay.classList.toggle("activo", abierto);
      btnMenuMovil.setAttribute("aria-expanded", abierto ? "true" : "false");
      document.body.classList.toggle("menu-abierto", abierto);
    };

    btnMenuMovil.addEventListener("click", abrirCerrarMenu);
    overlay.addEventListener("click", abrirCerrarMenu);

    window.addEventListener("resize", function () {
      if (window.innerWidth > 900) {
        sidebar.classList.remove("abierto");
        overlay.classList.remove("activo");
        btnMenuMovil.setAttribute("aria-expanded", "false");
        document.body.classList.remove("menu-abierto");
      }
    });
  }
});
