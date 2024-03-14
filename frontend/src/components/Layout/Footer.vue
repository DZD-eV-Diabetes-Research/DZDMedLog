<template>
  <footer class="footer">
    <div class="footer__content">
      <div class="footer__logos">
        <img src="/img/logos/helmholtz.png" alt="Helmholtz Munich" />
      </div>
      <div class="footer__links">
        <a href="https://www.dzd-ev.de/footermenue/impressum/index.html" target="_new">Imprint</a>
      </div>
    </div>
  </footer>
</template>
<script>
export default {
  name: "Footer",
};
</script>
<style lang="scss">
@import "../../styles/mixins";
@import "../../styles/variables/breakpoints";
.footer {
  background-color: var(--primary1);
  width: 100%;
  font-size: var(--font-size-md);
  --link-color: var(--primary8);
  position: relative;
  bottom: 0;
}

.footer__content {
  @include container();
  margin: 0;
  padding: var(--space-4) var(--layout-padding-x);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  width: 100%;
}

.footer__logos {
  display: flex;
  flex-direction: row;
  align-items: flex-end;
  gap: var(--space-4);

  img {
    max-height: 60px;
  }
}

.footer__links {
  display: flex;
  flex-direction: row;
  gap: var(--space-2);
}
</style>