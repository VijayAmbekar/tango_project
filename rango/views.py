from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.template import Context, RequestContext
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from django.shortcuts import render_to_response, render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import datetime
from rango.bing_search import run_query
from rango.models import User, UserProfile

def index(request):
	context = RequestContext(request)
	context_dict = {'cat_list': get_category_list()}
	
	page_list = Page.objects.order_by('-views')[:5]
	context_dict['pages'] = page_list
	
	if request.user.is_authenticated:
		context_dict['user'] = request.user
	
	if request.session.get('last_visit'):
		last_visit_time = request.session.get('last_visit')
		visits = request.session.get('visits', 0)
		
		if (datetime.now() - datetime.strptime(last_visit_time[:-7],"%Y-%m-%d %H:%M:%S")).days > 0:
			request.session['visits'] = visits + 1
			request.session['last_visit'] =str(datetime.now())
	else:
		request.session['visits'] = 1
		request.session['last_visit'] =str(datetime.now())
		
	return render_to_response('rango/index.html',context_dict, context)
	
def about(request):
	t =get_template('rango/about.html')
	context_dict = {'cat_list': get_category_list()}
	context_dict['boldMessage'] = 'I am about\'s bold content from context'
	if request.user.is_authenticated:
		context_dict['user'] = request.user
		
	if request.session.get('visits'):
		context_dict['visits'] = request.session.get('visits')
	else:
		context_dict['visits'] = 0
	html = t.render(Context(context_dict))
	return HttpResponse(html)

def category(request, category_name_url):
	context = RequestContext(request)

	category_name = decode_url(category_name_url)
	
	context_dict = {'cat_list': get_category_list()}
	context_dict['category_name'] = category_name
	context_dict['category_name_url'] = category_name_url
	try:
		category = Category.objects.get(name__iexact=category_name)
		pages = Page.objects.filter(category=category)
		
		context_dict['category'] = category
		
		pages = Page.objects.filter(category=category).order_by('-views')
		context_dict['pages'] = pages
	except Category.DoesNotExist:
		pass
	
	if request.user.is_authenticated:
		context_dict['user'] = request.user
		
	if request.method == 'POST':
		query = request.POST['query'].strip()
		if query:
			result_list = run_query(query)
			context_dict['result_list'] = result_list
	
	return render_to_response('rango/category.html', context_dict, context)

def add_category(request):
    # Get the context from the request.
    context = RequestContext(request)

    # A HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)

        # Have we been provided with a valid form?
        if form.is_valid():
            # Save the new category to the database.
            form.save(commit=True)

            # Now call the index() view.
            # The user will be shown the homepage.
            return HttpResponseRedirect('/rango/') #index(request)
			# return HttpResponseRedirect('/rango/')
        else:
            # The supplied form contained errors - just print them to the terminal.
            print form.errors
    else:
        # If the request was not a POST, display the form to enter details.
        form = CategoryForm()
	
	context_dict = {'cat_list': get_category_list()}
	context_dict['form'] = form
	if request.user.is_authenticated:
		context_dict['user'] = request.user

    # Bad form (or form details), no form supplied...
    # Render the form with error messages (if any).
    return render_to_response('rango/add_category.html', context_dict, context)
	
def add_page(request, category_name_url):
	context = RequestContext(request)
	context_dict = {'cat_list': get_category_list()}
	category_name = decode_url(category_name_url)
	if request.method == 'POST':
		form = PageForm(request.POST)
		if form.is_valid():
			page = form.save(commit=False)
			
			try:
				cat = Category.objects.get(name=category_name)
				page.category = cat
			except Category.DoesNotExist:
				return render_to_response('rango/add_category.html', {}, context)
				
			page.views = 0
			page.save()
			return HttpResponseRedirect('/rango/category/' + category_name_url)
		else:
			context_dict['errors'] = form.errors
			print form.errors
	else:
		form = PageForm()
	
	context_dict['form'] = form
	context_dict['category_name_url'] = category_name_url
	if request.user.is_authenticated:
		context_dict['user'] = request.user
	return render_to_response('rango/add_page.html', context_dict, context)
	
def register(request):
	context = RequestContext(request)
	context_dict = {'cat_list': get_category_list()}
	registered = False
	if request.method == 'POST':
		user_form = UserForm(data=request.POST)
		profile_form = UserProfileForm(data=request.POST)
		
		if user_form.is_valid() and profile_form.is_valid():
			user = user_form.save()
			user.set_password(user.password)
			user.save()
			
			profile = profile_form.save(commit=False)
			profile.user = user
			if 'picture' in request.FILES:
				profile.picure = request.FILES['picture']
				profile.save()
				registered = True
		else:
			context_dict['errors'] = user_form.errors + profile_form.errors
	else:
		user_form = UserForm()
		profile_form = UserProfileForm()
		
	context_dict['user_form'] = user_form
	context_dict['profile_form'] = profile_form
	context_dict['registered'] = registered
	return render_to_response('rango/register.html', context_dict, context)
	
def user_login(request):
	context = RequestContext(request)
	context_dict = {'cat_list': get_category_list()}
	
	if request.user.is_authenticated:
		context_dict['user'] = request.user
		
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		
		user = authenticate(username = username, password = password)
		
		if user:
			if user.is_active:
				login(request, user)
				return HttpResponseRedirect('/rango/')
			else:
				context_dict['errors'] = "Your Rango account is disabled."
		else:
			context_dict['errors'] = "Invalid login credentials"
	else:
		context_dict['errors'] = ''
	
	return render_to_response('rango/login.html', context_dict, context)
		
		
@login_required
def restricted(request):
	return HttpResponse("Since you're logged in, you can see this text!")
	
@login_required
def user_logout(request):
	logout(request)
	return HttpResponseRedirect('/rango/')
	
def search(request):
	context = RequestContext(request)
	context_dict = {'cat_list': get_category_list()}
	result_list = []
	
	if request.method == 'POST':
		query = request.POST['query'].strip()
		if query:
			result_list = run_query(query)
			
	context_dict['result_list'] = result_list
	return render_to_response('rango/search.html', context_dict, context)

@login_required
def profile(request):
	context = RequestContext(request)
	context_dict = {'cat_list': get_category_list()}
	u = User.objects.get(username=request.user)
	
	try:
		up = UserProfile.object.get(user = u)
	except:
		up = None
		
	context_dict['user'] = u
	context_dict['userprofile'] = up
	return render_to_response('rango/profile.html', context_dict, context)
	
def track_url(request):
	context = RequestContext(request)
	page_id = None
	url = '/rango/'
	if request.method == 'GET':
		if 'page_id' in request.GET:
			page_id = request.GET['page_id']
			try:
				page = Page.objects.get(id = page_id)
				page.views = page.views + 1
				page.save()
				url = page.url
			except:
				pass
				
	return HttpResponseRedirect(url)
	
# def get_category_list():
	# category_list = Category.objects.order_by('-likes')[:5]
	# for category in category_list:
		# category.url = encode_url(category.name)
	# return category_list
	
@login_required
def like_category(request):
	likes = 0
	if request.method == 'GET':
		if 'category_id' in request.GET:
			category_id = request.GET['category_id']
			try:
				category = Category.objects.get(id=int(category_id))
				likes = category.likes + 1
				category.likes = likes
				category.save()
			except:
				print "Some error occured"
				
	return HttpResponse(likes)

def get_category_list(max_results=0, starts_with=''):
	cat_list = []
	if starts_with:
		cat_list = Category.objects.filter(name__istartswith=starts_with)
	else:
		cat_list = Category.objects.all()
		
	if max_results > 0:
		if len(cat_list) > max_results:
			cat_list = cat_list[:max_results]
			
	for cat in cat_list:
		cat.url = encode_url(cat.name)
		
	return cat_list
	
def suggest_category(request):
	context = RequestContext(request)
	cat_list = []
	starts_with = ''
	if request.method == 'GET':
		starts_with = request.GET['suggestion']
		
	cat_list = get_category_list(8, starts_with)
	return render_to_response('rango/category_list.html', {'cat_list': cat_list}, context);
	
def auto_add_page(request):
	context = RequestContext(request)
	context_dict = {}
	
	if request.method == 'GET':
		category_id = request.GET['category_id'];
		title = request.GET['title'];
		url = request.GET['url'];
		
		if category_id:
			category = Category.objects.get(id=int(category_id))
			
			if category:
				p = Page.objects.get_or_create(category=category, title=title, url=url);
				pages = Page.objects.filter(category=category).order_by('-views')
				
				context_dict['pages'] = pages
				
	return render_to_response('rango/page_list.html', context_dict, context)
				
			
	
def encode_url(url):
	return url.replace(' ', '_')
	
def decode_url(url):
	return url.replace('_', ' ')