
def arquivo_planilha_path(instance, filename):
    return f'static/planos/{instance.pk}.xlsx'  # Nome fixo: <id>.xlsx
