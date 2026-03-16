/* =============================================================
   Library Management System — Client-Side Scripts
   jQuery + Bootstrap 5
   ============================================================= */

$(function () {

  /* ----- Bootstrap Tooltips Init ----- */
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.forEach(function (el) {
    new bootstrap.Tooltip(el);
  });

  /* =================================================================
     FORM VALIDATION
     ================================================================= */

  // Helper: show / clear error on a field
  function showError($field, msg) {
    $field.addClass('is-invalid');
    $field.siblings('.invalid-feedback').text(msg);
  }
  function clearError($field) {
    $field.removeClass('is-invalid');
    $field.siblings('.invalid-feedback').text('');
  }

  // Email regex
  var emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  /* ---------- Login Form ---------- */
  $('#loginForm').on('submit', function (e) {
    var valid = true;
    var $email = $('#loginEmail');
    var $pass  = $('#loginPassword');

    clearError($email);
    clearError($pass);

    if (!$email.val().trim()) {
      showError($email, 'Please enter your email address.');
      valid = false;
    } else if (!emailRe.test($email.val().trim())) {
      showError($email, 'Please enter a valid email address.');
      valid = false;
    }

    if (!$pass.val()) {
      showError($pass, 'Please enter your password.');
      valid = false;
    } else if ($pass.val().length < 6) {
      showError($pass, 'Password must be at least 6 characters.');
      valid = false;
    }

    if (!valid) e.preventDefault();
  });

  /* ---------- Register Form ---------- */
  $('#registerForm').on('submit', function (e) {
    var valid = true;
    var $name    = $('#regName');
    var $email   = $('#regEmail');
    var $pass    = $('#regPassword');
    var $phone   = $('#regPhone');

    [$name, $email, $pass, $phone].forEach(function ($f) { clearError($f); });

    if (!$name.val().trim()) {
      showError($name, 'Full name is required.');
      valid = false;
    }

    if (!$email.val().trim()) {
      showError($email, 'Email address is required.');
      valid = false;
    } else if (!emailRe.test($email.val().trim())) {
      showError($email, 'Please enter a valid email.');
      valid = false;
    }

    if (!$phone.val().trim()) {
      showError($phone, 'Phone number is required.');
      valid = false;
    } else if (!/^\d{10}$/.test($phone.val().replace(/\D/g, ''))) {
      showError($phone, 'Please enter a valid 10-digit phone number.');
      valid = false;
    }

    if (!$pass.val()) {
      showError($pass, 'Password is required.');
      valid = false;
    } else if ($pass.val().length < 8) {
      showError($pass, 'Password must be at least 8 characters.');
      valid = false;
    }

    if (!valid) e.preventDefault();
  });

  /* ---------- Password Strength Indicator ---------- */
  $('#regPassword').on('input', function() {
    var val = $(this).val();
    var $container = $('#pwStrengthContainer');
    var $bar = $('#pwStrengthBar');
    var $text = $('#pwStrengthText');
    
    if (val.length === 0) {
      $container.hide();
      $text.hide();
      return;
    }
    
    $container.show();
    $text.show();
    
    var strength = 0;
    if (val.length >= 8) strength += 25;
    if (val.length >= 12) strength += 25;
    if (/[A-Z]/.test(val)) strength += 25;
    if (/[0-9]/.test(val) || /[^A-Za-z0-9]/.test(val)) strength += 25;
    
    $bar.css('width', strength + '%');
    
    if (strength <= 25) {
      $bar.removeClass('bg-warning bg-success').addClass('bg-danger');
      $text.text('Weak password').removeClass('text-warning text-success').addClass('text-danger');
    } else if (strength <= 50) {
      $bar.removeClass('bg-danger bg-success').addClass('bg-warning');
      $text.text('Medium password').removeClass('text-danger text-success').addClass('text-warning');
    } else {
      $bar.removeClass('bg-danger bg-warning').addClass('bg-success');
      $text.text('Strong password').removeClass('text-danger text-warning').addClass('text-success');
    }
  });

  /* ---------- Add Book Form (Admin) ---------- */
  $('#addBookForm').on('submit', function (e) {
    var valid = true;
    var $title  = $('#bookTitle');
    var $author = $('#bookAuthor');
    var $isbn   = $('#bookISBN');
    var $qty    = $('#bookQty');

    [$title, $author, $isbn, $qty].forEach(function ($f) { clearError($f); });

    if (!$title.val().trim()) {
      showError($title, 'Book title is required.');
      valid = false;
    }

    if (!$author.val().trim()) {
      showError($author, 'Author name is required.');
      valid = false;
    }

    if (!$isbn.val().trim()) {
      showError($isbn, 'ISBN is required.');
      valid = false;
    } else if ($isbn.val().trim().length < 10) {
      showError($isbn, 'ISBN must be at least 10 characters.');
      valid = false;
    }

    if (!$qty.val() || parseInt($qty.val(), 10) < 1) {
      showError($qty, 'Quantity must be at least 1.');
      valid = false;
    }

    if (!valid) e.preventDefault();
  });

  /* Clear validation state on input */
  $(document).on('input change', '.form-control, .form-select', function () {
    clearError($(this));
  });

  /* =================================================================
     TABLE SORT HEADERS (visual toggle only)
     ================================================================= */
  $('.table thead th[data-sort]').on('click', function () {
    var $th = $(this);
    var $allTh = $th.closest('thead').find('th');

    // Reset all others
    $allTh.not($th).removeClass('sorted asc desc');
    $allTh.not($th).find('.sort-icon')
      .removeClass('bi-sort-up bi-sort-down')
      .addClass('bi-arrow-down-up');

    // Toggle current
    if ($th.hasClass('asc')) {
      $th.removeClass('asc').addClass('sorted desc');
      $th.find('.sort-icon').removeClass('bi-sort-up bi-arrow-down-up').addClass('bi-sort-down');
    } else {
      $th.removeClass('desc').addClass('sorted asc');
      $th.find('.sort-icon').removeClass('bi-sort-down bi-arrow-down-up').addClass('bi-sort-up');
    }
  });

  /* =================================================================
     PAGINATION (visual active toggle)
     ================================================================= */
  $('.pagination .page-link').on('click', function (e) {
    e.preventDefault();
    $(this).closest('.pagination').find('.page-item').removeClass('active');
    $(this).closest('.page-item').addClass('active');
  });

  /* =================================================================
     MISC UI
     ================================================================= */

  // Confirm before removing a book
  $(document).on('click', '.btn-remove-book', function (e) {
    if (!confirm('Are you sure you want to remove this book?')) {
      e.preventDefault();
    }
  });

  // Simulate send-reminder click on Admin Dashboard
  $(document).on('click', '.btn-send-reminder', function () {
    var $btn = $(this);
    var user = $btn.data('user') || 'the user';
    var title = $btn.data('title') || 'this book';
    
    // Change button state to sending
    $btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-1"></span>Sending…');
    
    // Simulate ajax delay
    setTimeout(function () {
      $btn.html('<i class="bi bi-check-circle me-1"></i>Sent');
      $btn.removeClass('btn-outline-warning btn-warning').addClass('btn-success');
      
      // Optional: Show a quick toast or alert
      // alert('Reminder sent to ' + user + ' for "' + title + '".');
    }, 1200);
  });

  // Admin Dashboard Delete Confirmation Modal
  var bookToDelete = null;
  $(document).on('click', '.btn-remove-book', function () {
    var title = $(this).data('title');
    $('#deleteBookTitle').text('"' + title + '"');
    bookToDelete = $(this).closest('tr');
  });

  $(document).on('click', '#confirmDeleteBtn', function() {
    var $btn = $(this);
    $btn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-1"></span>Removing…');
    
    setTimeout(function() {
      if (bookToDelete) {
        bookToDelete.fadeOut(400, function() {
          $(this).remove();
        });
      }
      $('#deleteConfirmModal').modal('hide');
      $btn.prop('disabled', false).html('<i class="bi bi-trash me-1"></i>Remove');
    }, 800);
  });

  // Confirm issuing a book
  $(document).on('click', '.btn-issue-book', function (e) {
    var title = $(this).data('title');
    if (confirm('Are you sure you want to issue "' + title + '"?')) {
      // Typically an ajax call or form submission would happen here.
      // For this static preview, we'll just show an alert or redirect to the success page.
      window.location.href = '/success';
    } else {
      e.preventDefault();
    }
  });

  /* =================================================================
     CATALOG PAGE FILTERING & SEARCH
     ================================================================= */
  var $searchInput = $('#catalogSearch');
  var $categoryFilter = $('#catalogCategory');
  var $bookItems = $('.book-item');
  var $noResultsMsg = $('#noResultsMsg');

  function filterCatalog() {
    // If not on the catalog page, exit
    if ($searchInput.length === 0) return;

    var query = $searchInput.val().toLowerCase().trim();
    var category = $categoryFilter.val().toLowerCase();
    var visibleCount = 0;

    $bookItems.each(function() {
      var $item = $(this);
      var itemTitle = $item.data('title') || "";
      var itemAuthor = $item.data('author') || "";
      var itemCategory = $item.data('category') || "";

      // Check category match
      var categoryMatch = (category === 'all' || itemCategory === category);
      
      // Check search match
      var searchMatch = (itemTitle.indexOf(query) !== -1 || itemAuthor.indexOf(query) !== -1);

      if (categoryMatch && searchMatch) {
        $item.fadeIn(300);
        visibleCount++;
      } else {
        $item.fadeOut(300);
      }
    });

    // Handle "no results" state
    setTimeout(function() {
      if (visibleCount === 0) {
        $noResultsMsg.removeClass('d-none').hide().fadeIn(300);
      } else {
        $noResultsMsg.fadeOut(200, function() {
          $(this).addClass('d-none');
        });
      }
    }, 310);
  }

  // Bind events for filtering
  $searchInput.on('keyup', filterCatalog);
  $categoryFilter.on('change', filterCatalog);

  // Auto-dismiss alerts after 5 s
  setTimeout(function () {
    $('.alert-dismissible').alert('close');
  }, 5000);

  // Smooth scroll for internal links (Admin Sidebar)
  $('a.nav-link[href^="#"]').on('click', function(e) {
    var target = $(this.getAttribute('href'));
    if( target.length ) {
        e.preventDefault();
        $('html, body').stop().animate({
            scrollTop: target.offset().top - 20
        }, 500);
    }
  });

});
