# ABCES
```
Extract out the contact information. Always output all of (and only) these fields:

* Page Number
* Company Name
* Address
* Phone
* First Name
* Last Name
* Title
* Contact Email

Use the below as an example - the content should be parsed into fields as follows - double check accuracy for field/column alignment:

Input Example 1:
A REBAR, INC.
205 Sills Road
P O Box 1310
Yonkers, NY 11980
555-555-5555 Phone
Region 8 - Specialty
Andy Sos, President
sos@arebar.com
www.arebar.com

Output Preparation Example 1:
*Company Name*: A REBAR, INC.
*Address*: 205 Sills Road
P O Box 1310
Yonkers, NY 11980
*Phone:* 555-555-5555
*First Name:* Andy
*Last Name:* Sos
*Title:* President
*Contact Email:* sos@arebar.com

Input Example 2:
Gernatt Asphalt Products, Inc.
BILL SCHMIT
13870 Taylor Hollow Road
Collins, NY 14034
p: (555) 555-5555 • f: (716) 532-9000
e: billy@gernatt.com
w: www.gernatt.com

Output Preparation Example 2:
*Company Name*: Gernatt Asphalt Products, Inc.
*Address*: 13870 Taylor Hollow Road Collins, NY 14034
Yonkers, NY 11980
*Phone:* 555-555-5555
*First Name:* Bill
*Last Name:* Schmit
*Title:* Not Found
*Contact Email:* billy@gernatt.com

If no Title exists, use Not Found.
```

# AGCNY
```
Extract out the contact information. Always output all of (and only) these fields:

* Page Number
* Company Name
* Address
* Phone
* First Name
* Last Name
* Title
* Contact Email

Use the below as an example - the content should be parsed into fields as follows - double check accuracy for field/column alignment:

Input:
A REBAR, INC.
205 Sills Road
P O Box 1310
Yonkers, NY 11980
555-555-5555 Phone
Region 8 - Specialty
Andy Sos, President
sos@arebar.com
www.arebar.com

Output Preparation:
*Company Name*: A REBAR, INC.
*Address*: 205 Sills Road
P O Box 1310
Yonkers, NY 11980
*Phone:* 555-555-5555
*First Name:* Andy
*Last Name:* Sos
*Title:* President
*Contact Email:* sos@arebar.com
```

# CONEXBUFFNY
```
Extract out the contact information. Always output all of (and only) these fields:

* Page Number
* Company Name
* Address
* Phone
* First Name
* Last Name
* Title
* Contact Email

Use the below as an example - the content should be parsed into fields as follows - double check accuracy for field/column alignment. Start below "Members" for each page:

 Input:
1895 Electric LLC
Matt Wawy
6 0 School Street, Unit 1114
Orchard Park, NY 14127
E: mwawy@gmail.com
T: (555) 555-5555 

Output Preparation:
*Company Name*: 1895 Electric LLC
*Address*: 6 0 School Street, Unit 1114
Orchard Park, NY 14127
*Phone:* (555) 555-5555 
*First Name:* Matt
*Last Name:* Wawy
*Contact Email:* mwawy@gmail.com
```
