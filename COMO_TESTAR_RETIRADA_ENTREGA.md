# 📦 Como Testar o Sistema de Retirada/Entrega

## ✅ Passo a Passo Completo

### 🔧 Passo 1: Configurar o Local de Retirada (Admin)

1. **Faça login como administrador**
   - Email: `admin@ecommerce.com`
   - Senha: `admin123`

2. **Acesse as Configurações da Loja**
   - No menu do usuário (canto superior direito), clique em **"Painel Admin"**
   - No menu lateral, clique em **"Configurações"**

3. **Preencha o Local de Retirada**
   - Localize o campo **"Local de Retirada (opcional)"**
   - Preencha com o endereço e horários, exemplo:
   ```
   Rua das Flores, 123 - Centro
   Cidade Exemplo - SP
   CEP: 12345-678
   
   Horário de Retirada:
   Seg-Sex: 9h às 18h
   Sáb: 9h às 13h
   ```

4. **Salve as configurações**
   - Clique no botão **"Salvar Configurações"**
   - Uma mensagem de sucesso será exibida

**⚠️ IMPORTANTE**: Sem configurar o local de retirada, apenas a opção de entrega em casa estará disponível!

---

### 🛒 Passo 2: Testar o Checkout (Cliente)

1. **Faça login como cliente** (ou crie uma nova conta)
   - Email de teste: `cliente@teste.com`
   - Senha: `senha123`

2. **Adicione produtos ao carrinho**
   - Navegue pela loja
   - Clique em "Ver Detalhes" em um produto
   - Clique em "Adicionar ao Carrinho"

3. **Vá para o checkout**
   - Clique no ícone do carrinho no topo
   - Clique em "Finalizar Compra"

4. **Escolha o tipo de entrega** ✨
   
   Agora você verá **duas opções**:
   
   **🚚 Entrega em Casa**
   - Selecione esta opção se quiser receber no endereço
   - Preencha o campo "Endereço de Entrega" com o endereço completo
   
   **🏪 Retirar no Local**
   - Selecione esta opção para retirada pessoal
   - O endereço de retirada será exibido automaticamente
   - Não precisa preencher endereço de entrega

5. **Complete o pedido**
   - Escolha o método de pagamento
   - Adicione observações (opcional)
   - Clique em "Confirmar Pedido"

---

### 📊 Passo 3: Gerenciar Pedidos (Admin)

1. **Acesse o painel de pedidos**
   - Faça login como admin
   - Vá em **"Painel Admin"** > **"Pedidos"**

2. **Identifique o tipo de pedido**
   - Pedidos de **Entrega** têm o ícone 🚚
   - Pedidos de **Retirada** têm o ícone 🏪

3. **Atualize o status do pedido**
   - Clique em "Ver Detalhes" no pedido
   - Selecione o novo status:
   
   **Para pedidos de ENTREGA:**
   - ⏳ Pendente
   - ✅ Confirmado
   - 📦 Em Separação
   - 🚚 Saiu para Entrega
   - 🎉 Entregue
   
   **Para pedidos de RETIRADA:**
   - ⏳ Pendente
   - ✅ Confirmado
   - 📦 Em Separação
   - ✨ Pronto para Retirada
   - 🎉 Retirado

4. **Receba notificações em tempo real** 🔔
   - Badge vermelho com contagem de pedidos pendentes
   - Pop-up visual na tela quando chega novo pedido
   - Notificação push do navegador (se permitido)
   - Som de alerta

---

## 🎯 Resumo Rápido

### O que foi implementado:
✅ Opção de escolher entre Retirada ou Entrega no checkout  
✅ Campo de local de retirada nas configurações da loja  
✅ Status inteligentes baseados no tipo de entrega  
✅ Sistema de notificações em tempo real para novos pedidos  
✅ Interface responsiva e intuitiva  

### Credenciais de Teste:
- **Admin**: `admin@ecommerce.com` / `admin123`
- **Cliente**: `cliente@teste.com` / `senha123`

---

## 🚨 Solução de Problemas

**Problema**: Não aparece a opção de Retirada/Entrega no checkout  
**Solução**: Certifique-se de que o admin configurou o "Local de Retirada" nas Configurações da Loja

**Problema**: Notificações não aparecem  
**Solução**: Permita notificações do navegador quando solicitado (apenas para admin)

**Problema**: Badge de notificações não atualiza  
**Solução**: Aguarde até 10 segundos (verificação automática) ou recarregue a página

---

**Desenvolvido por João Layon** 🚀
