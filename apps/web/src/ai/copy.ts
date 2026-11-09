export const aiErrors: Record<string, string> = {
  AI_STANDING_AUTHORIZATION_REQUIRED:
    'Activează autorizarea permanentă în Setări → Modele AI. Solicitarea nu a fost autorizată.',
  AI_STANDING_SCOPE_REFUSED:
    'Rolul, operațiunea sau categoria de date nu intră în autorizarea permanentă. Revizuiește domeniul în Setări.',
  AI_STANDING_SCOPE_CHANGED:
    'Destinația sau politica cloud s-a schimbat. Revizuiește autorizarea permanentă cu MFA.',
  AI_STANDING_CONNECTION_UNAVAILABLE: 'Conexiunea autorizată lipsește sau este dezactivată.',
  AI_STANDING_BUDGET_INVALID:
    'Limitele pe solicitare, zi și lună trebuie să fie pozitive și ordonate în limitele platformei.',
  AI_STANDING_SCOPE_INVALID: 'Domeniul autorizării conține valori duplicate sau nepermise.',
  AI_WORKER_UNAVAILABLE:
    'Worker-ul nu are un heartbeat recent confirmat. Verifică serviciul și reîncarcă starea.',
  AI_OWNER_REQUIRED: 'Numai proprietarul autentificat poate solicita analiza.',
  AI_CONTEXT_BUDGET_UNVERIFIED:
    'Capacitatea verificată a modelului nu acoperă dimensiunea solicitată.',
  AI_REMOTE_CONTEXT_POLICY_REFUSED:
    'Politica acestei conexiuni nu permite categoria de date la distanță. Revizuiește explicit configurația.',

  AI_PROVIDER_REQUEST_REFUSED:
    'Furnizorul a refuzat o cerere HTTP. Acest cod generic nu identifică singur cauza; consultă statusul și etapa de mai jos, dacă au fost păstrate.',
  AI_CLOUD_OPERATOR_OPT_IN_REQUIRED:
    'OpenRouter este dezactivat de operator. Configurează explicit politica cloud și proxy-ul; aprobarea privată rămâne separată.',
  AI_CLOUD_AUTHORIZATION_REQUIRED:
    'Înregistrează mai întâi autorizarea cloud OpenRouter în Setări.',
  AI_CLOUD_EXPLICIT_CONSENT_REQUIRED:
    'Lipsește aprobarea explicită pentru cloud public. Politica privată nu o înlocuiește.',
  AI_CREDENTIAL_REQUIRED:
    'Lipsește cheia OpenRouter. Salveaz-o numai pe server, apoi verifică modelul.',
  AI_CLOUD_AUTHORIZATION_OR_KEY_UNAVAILABLE:
    'Politica cloud sau cheia separată de criptare nu este disponibilă. Verifică instalarea AI.',
  AI_CLOUD_COST_ACKNOWLEDGEMENT_REQUIRED:
    'Această verificare sau analiză poate avea costuri. Revizuiește limita și bifează aprobarea solicitării cloud.',
  AI_CLOUD_BUDGET_EXCEEDED:
    'Limita conservatoare pe solicitare, zi sau lună a fost atinsă. Verifică rezervările; nu repetăm automat cereri cu rezultat incert.',
  AI_CLOUD_FALLBACK_PROHIBITED:
    'OpenRouter necesită un singur model și furnizor aprobat, fără alternative automate.',
  AI_PROVIDER_AUTH_REFUSED:
    'OpenRouter a refuzat autentificarea. Verifică cheia în contul furnizorului și salvează o cheie validă pe server.',
  AI_PROVIDER_CREDIT_REQUIRED:
    'OpenRouter a refuzat solicitarea din cauza creditului. Verifică soldul și limita cheii la furnizor; nu reîncercăm automat.',
  AI_APPROVED_UPSTREAM_UNAVAILABLE:
    'Catalogul nu confirmă furnizorul ales pentru acest model. Verifică tag-ul exact; nu schimbăm automat furnizorul.',
  AI_APPROVED_UPSTREAM_NOT_ZDR:
    'Modelul există, dar furnizorul aprobat nu apare în catalogul ZDR pentru el. Revizuiește explicit furnizorul autorizat; nu dezactivăm ZDR și nu alegem automat o alternativă. Nu a fost trimisă generarea din această probă.',
  AI_APPROVED_PARAMETERS_UNAVAILABLE:
    'Furnizorul aprobat nu declară suportul necesar pentru răspuns structurat strict și parametrii probei. Verifică un furnizor compatibil; nu eliminăm validarea și nu trimitem generarea.',
  AI_EXACT_MODEL_ID_REQUIRED:
    'Folosește un identificator exact autor/model. Routerele automate nu sunt permise.',
  AI_PROVIDER_DESTINATION_MISMATCH:
    'Protocolul nu corespunde destinației. Pentru OpenRouter folosește protocolul OpenAI compatibil dedicat.',

  AI_NOT_CONFIGURED:
    'Analiza privată nu este configurată. Operatorul trebuie să pregătească cheia separată și worker-ul.',
  AI_MODEL_REQUIRES_VERIFICATION:
    'Verificarea modelului lipsește sau a expirat. Rulează din nou verificarea în Setări.',
  AI_MODEL_OR_CONNECTION_UNAVAILABLE:
    'Modelul sau conexiunea nu poate fi folosită. Verifică destinația, autorizarea și proba curentă.',
  AI_ROLE_NOT_CONFIGURED: 'Acest rol nu are un model ales. Configurează rolul în Setări.',
  AI_QUOTA_REACHED:
    'Limita de solicitări a fost atinsă. Verifică activitatea; nu retrimite cereri duplicate.',
  AI_CONTEXT_NOT_AVAILABLE:
    'Contextul nu este accesibil sau este protejat. Alege o referință permisă din contul tău.',
  AI_CONTEXT_REQUIRES_COMPLETED_EXPERIMENT:
    'Testul nu are încă un rezultat final stocat. Așteaptă finalizarea sa.',
  AI_CONTEXT_BYTE_LIMIT:
    'Contextul este prea mare. Alege o singură referință sau un rezumat mai mic.',
  AI_CONTEXT_TIER_UNAVAILABLE:
    'Nivelul de context nu este activat pe server. Alege AUTO sau un nivel configurat.',
  AI_CONTEXT_REVISION_MUST_INCREASE:
    'Alege un plafon mai mare pentru versiunea nouă. Modelul existent nu este modificat.',
  AI_REQUEST_BYTE_LIMIT:
    'Cererea depășește limita JSON de64KiB. Redu întrebarea sau numărul referințelor.',
  AI_CONTEXT_BUDGET_EXCEEDED:
    'Întrebarea, documentația și schema răspunsului nu încap în fereastra aprobată. Cererea nu a fost trimisă modelului. Poți edita întrebarea, alege un context mai mic sau un model cu o capacitate mai mare verificată în Setări.',
  AI_INPUT_BYTE_LIMIT:
    'Datele pregătite depășesc limita de intrare a platformei. Cererea nu a fost trimisă modelului; redu contextul sau întrebarea.',
  AI_REMOTE_POLICY_REQUIRED:
    'Destinația este la distanță. Proprietarul trebuie să aprobe separat politica de procesare.',
  AI_REMOTE_PROCESSING_NOT_APPROVED:
    'Contextul nu este aprobat pentru această infrastructură la distanță. Folosește o destinație locală permisă.',
  AI_IDEMPOTENCY_CONFLICT:
    'Cheia aparține unei alte solicitări. Verifică activitatea înainte de a crea un draft nou.',
  AI_PROVIDER_UNAVAILABLE:
    'Serverul de inferență nu răspunde. Verifică serviciul și conectivitatea privată.',
  AI_OUTPUT_SCHEMA_INVALID:
    'Răspunsul nu respectă forma cerută. Nu a fost publicat ca analiză utilizabilă.',
  AI_HALLUCINATED_REFERENCE:
    'Modelul a citat o referință care nu i-a fost oferită. Răspunsul a fost refuzat.',
  AI_TOOL_SUGGESTION_REFUSED:
    'Modelul a cerut folosirea unui instrument. Gateway-ul nu execută astfel de cereri.',
  AI_PROVIDER_COMPLETION_UNKNOWN:
    'Nu putem confirma rezultatul furnizorului. Nu repetăm automat o analiză posibil deja procesată.',
};
