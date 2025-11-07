# Guarantor System Implementation TODO

## Phase 1: Models & Database
- [ ] Add Guarantor model to models.py
- [ ] Add LoanApplication model to models.py
- [ ] Update Loan model with guarantor methods
- [ ] Create and run migrations

## Phase 2: Admin Interface
- [ ] Add GuarantorAdmin to admin.py
- [ ] Add LoanApplicationAdmin to admin.py
- [ ] Update LoanAdmin with guarantor fields

## Phase 3: API Serializers
- [ ] Add GuarantorSerializer to serializers.py
- [ ] Add LoanApplicationSerializer to serializers.py
- [ ] Add AvailableGuarantorSerializer to serializers.py
- [ ] Update LoanSerializer with guarantor fields

## Phase 4: API Views
- [ ] Add GuarantorListView to views.py
- [ ] Add GuarantorDetailView to views.py
- [ ] Add available_guarantors API view
- [ ] Add add_guarantor API view
- [ ] Add approve_guarantor API view
- [ ] Add LoanApplicationView to views.py
- [ ] Add submit_loan_application API view
- [ ] Update LoanDetailView with guarantor serializer

## Phase 5: URLs
- [ ] Update urls.py with guarantor endpoints
- [ ] Update urls.py with application endpoints

## Phase 6: Testing
- [ ] Test guarantor creation and eligibility
- [ ] Test loan application workflow
- [ ] Test admin interface
- [ ] Test API endpoints
