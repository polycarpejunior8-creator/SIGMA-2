"""
Catalogue des permissions du système (cf §11.2).
Ce catalogue est fourni par le développeur ; ce sont les POSTES qui combinent ces
permissions (et leurs périmètres) qui sont, eux, entièrement configurables par l'école.

Format de code : "module.action"
"""

PERMISSIONS_CATALOG: list[dict] = [
    # --- Élèves ---
    {"code": "students.view", "module": "students", "label_fr": "Consulter les élèves", "label_en": "View students"},
    {"code": "students.create", "module": "students", "label_fr": "Créer un élève", "label_en": "Create student"},
    {"code": "students.edit", "module": "students", "label_fr": "Modifier un élève", "label_en": "Edit student"},
    {"code": "students.archive", "module": "students", "label_fr": "Archiver un élève", "label_en": "Archive student"},
    {"code": "students.transfer", "module": "students", "label_fr": "Transférer un élève", "label_en": "Transfer student"},
    {"code": "students.delete", "module": "students", "label_fr": "Supprimer un élève", "label_en": "Delete student"},

    # --- Académique ---
    {"code": "grades.view", "module": "academic", "label_fr": "Consulter les notes", "label_en": "View grades"},
    {"code": "grades.enter", "module": "academic", "label_fr": "Saisir les notes", "label_en": "Enter grades"},
    {"code": "grades.edit", "module": "academic", "label_fr": "Modifier les notes", "label_en": "Edit grades"},
    {"code": "grades.validate", "module": "academic", "label_fr": "Valider les notes", "label_en": "Validate grades"},
    {"code": "grades.lock", "module": "academic", "label_fr": "Verrouiller les notes", "label_en": "Lock grades"},
    {"code": "report_cards.generate", "module": "academic", "label_fr": "Générer les bulletins", "label_en": "Generate report cards"},
    {"code": "report_cards.publish", "module": "academic", "label_fr": "Publier les bulletins", "label_en": "Publish report cards"},
    {"code": "honor_boards.manage", "module": "academic", "label_fr": "Gérer les tableaux d'honneur", "label_en": "Manage honor boards"},
    {"code": "honor_boards.view", "module": "academic", "label_fr": "Consulter les tableaux d'honneur", "label_en": "View honor boards"},
    {"code": "classes.manage", "module": "academic", "label_fr": "Gérer les classes", "label_en": "Manage classes"},
    {"code": "subjects.manage", "module": "academic", "label_fr": "Gérer les matières", "label_en": "Manage subjects"},
    {"code": "teacher_assignments.manage", "module": "academic", "label_fr": "Gérer les affectations enseignants", "label_en": "Manage teacher assignments"},
    {"code": "timetable.view", "module": "academic", "label_fr": "Consulter l'emploi du temps", "label_en": "View timetable"},
    {"code": "timetable.manage", "module": "academic", "label_fr": "Gérer l'emploi du temps", "label_en": "Manage timetable"},

    # --- Vie scolaire ---
    {"code": "attendance.view", "module": "attendance", "label_fr": "Consulter les présences/absences", "label_en": "View attendance"},
    {"code": "attendance.record", "module": "attendance", "label_fr": "Enregistrer une absence", "label_en": "Record attendance"},
    {"code": "attendance.justify", "module": "attendance", "label_fr": "Justifier une absence", "label_en": "Justify absence"},
    {"code": "discipline.view", "module": "discipline", "label_fr": "Consulter la discipline", "label_en": "View discipline"},
    {"code": "discipline.record", "module": "discipline", "label_fr": "Enregistrer une sanction/observation", "label_en": "Record disciplinary record"},

    # --- Finance ---
    {"code": "finance.view_payments", "module": "finance", "label_fr": "Consulter les paiements", "label_en": "View payments"},
    {"code": "finance.record_payment", "module": "finance", "label_fr": "Enregistrer un paiement", "label_en": "Record payment"},
    {"code": "finance.edit_payment", "module": "finance", "label_fr": "Modifier un paiement", "label_en": "Edit payment"},
    {"code": "finance.cancel_payment", "module": "finance", "label_fr": "Annuler un paiement", "label_en": "Cancel payment"},
    {"code": "finance.print_receipt", "module": "finance", "label_fr": "Imprimer un reçu", "label_en": "Print receipt"},
    {"code": "finance.view_cash_register", "module": "finance", "label_fr": "Consulter la caisse", "label_en": "View cash register"},
    {"code": "finance.close_cash_register", "module": "finance", "label_fr": "Effectuer une clôture de caisse", "label_en": "Close cash register"},
    {"code": "finance.manage_fee_structures", "module": "finance", "label_fr": "Gérer les tarifs/frais", "label_en": "Manage fee structures"},

    # --- Ressources humaines & Paie ---
    {"code": "hr.view_staff", "module": "hr", "label_fr": "Consulter le personnel", "label_en": "View staff"},
    {"code": "hr.manage_contracts", "module": "hr", "label_fr": "Gérer les contrats", "label_en": "Manage contracts"},
    {"code": "hr.request_leave", "module": "hr", "label_fr": "Demander un congé", "label_en": "Request leave"},
    {"code": "hr.approve_leave", "module": "hr", "label_fr": "Approuver/refuser un congé", "label_en": "Approve/reject leave"},
    {"code": "payroll.view", "module": "hr", "label_fr": "Consulter les fiches de paie", "label_en": "View payroll"},
    {"code": "payroll.manage", "module": "hr", "label_fr": "Générer/modifier les fiches de paie", "label_en": "Manage payroll"},

    # --- Administration ---
    {"code": "users.view", "module": "admin", "label_fr": "Consulter les utilisateurs", "label_en": "View users"},
    {"code": "users.create", "module": "admin", "label_fr": "Créer un utilisateur", "label_en": "Create user"},
    {"code": "users.edit", "module": "admin", "label_fr": "Modifier un utilisateur", "label_en": "Edit user"},
    {"code": "posts.manage", "module": "admin", "label_fr": "Créer/modifier les postes", "label_en": "Manage posts"},
    {"code": "permissions.manage", "module": "admin", "label_fr": "Modifier les permissions des postes", "label_en": "Manage post permissions"},
    {"code": "delegations.manage", "module": "admin", "label_fr": "Créer/révoquer des délégations", "label_en": "Manage delegations"},
    {"code": "audit.view", "module": "admin", "label_fr": "Consulter le journal d'audit", "label_en": "View audit log"},
    {"code": "schools.manage", "module": "admin", "label_fr": "Gérer les établissements/campus", "label_en": "Manage schools/campuses"},
    {"code": "academic_years.manage", "module": "admin", "label_fr": "Gérer les années scolaires", "label_en": "Manage academic years"},

    # --- Communication ---
    {"code": "communication.send", "module": "communication", "label_fr": "Envoyer des annonces/notifications", "label_en": "Send announcements/notifications"},
]
